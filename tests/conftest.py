import asyncio
import functools
import logging
import typing

import pytest

import HABApp
import tests
from HABApp.core.asyncio import async_context
from HABApp.core.const.topics import TOPIC_ERRORS
from HABApp.core.internals import setup_internals, EventBus, ItemRegistry
from tests.helpers import params, parent_rule, sync_worker, eb, get_dummy_cfg, LogCollector
from tests.helpers.log.log_matcher import LogLevelMatcher, AsyncDebugWarningMatcher

if typing.TYPE_CHECKING:
    parent_rule = parent_rule
    params = params
    sync_worker = sync_worker
    eb = eb


def raise_err(func):
    # return async wrapper
    if asyncio.iscoroutinefunction(func) or asyncio.iscoroutine(func):
        @functools.wraps(func)
        async def a(*args, **kwargs):
            return await func(*args, **kwargs)
        return a

    @functools.wraps(func)
    def f(*args, **kwargs):
        return func(*args, **kwargs)

    return f


@pytest.fixture(autouse=True, scope='function')
def show_errors(monkeypatch):
    # Patch the wrapper so that we always raise the exception
    monkeypatch.setattr(HABApp.core.wrapper, 'ignore_exception', raise_err)
    monkeypatch.setattr(HABApp.core.wrapper, 'log_exception', raise_err)


@pytest.fixture(autouse=True, scope='function')
def use_dummy_cfg(monkeypatch):
    cfg = get_dummy_cfg()
    monkeypatch.setattr(HABApp, 'CONFIG', cfg)
    monkeypatch.setattr(HABApp.config, 'CONFIG', cfg)
    monkeypatch.setattr(HABApp.config.config, 'CONFIG', cfg)
    yield cfg


@pytest.fixture(autouse=True, scope='session')
def event_loop():
    token = async_context.set('pytest')

    yield HABApp.core.const.loop

    async_context.reset(token)


@pytest.fixture(scope='function')
def ir():
    ir = ItemRegistry()
    yield ir


@pytest.fixture(autouse=True, scope='function')
def clean_objs(ir: ItemRegistry, eb: EventBus, request):
    markers = request.node.own_markers
    for marker in markers:
        if marker.name == 'no_internals':
            yield None
            return None

    restore = setup_internals(ir, eb, final=False)

    yield

    for name in ir.get_item_names():
        ir.pop_item(name)

    for r in restore:
        r.restore()


@pytest.fixture(autouse=True, scope='function')
def test_logs(caplog, request):
    caplog.set_level(logging.DEBUG)

    c = LogCollector(caplog)

    # This seems to be an asyncio issue (that a subprocess can block)
    c.rec_ignored.append(AsyncDebugWarningMatcher())

    yield c

    additional_ignores: typing.List[LogLevelMatcher] = []

    markers = request.node.own_markers
    for marker in markers:
        if marker.name == 'ignore_log_errors':
            additional_ignores.append(LogLevelMatcher(logging.ERROR))
        elif marker.name == 'ignore_log_warnings':
            additional_ignores.append(LogLevelMatcher(logging.WARNING))

    if additional_ignores:
        c.rec_expected.extend(additional_ignores)

    c.assert_ok()
