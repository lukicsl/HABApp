import asyncio
import logging
import typing

import HABApp
from HABApp.core.const import loop
from HABApp.core.events import ItemNoChangeEvent, ItemNoUpdateEvent, EventFilter
from HABApp.core.lib import PendingFuture

log = logging.getLogger('HABApp')


class BaseWatch(HABApp.rule_ctx.RuleBoundCancelObj):
    EVENT: typing.Union[typing.Type[ItemNoUpdateEvent], typing.Type[ItemNoChangeEvent]]

    def __init__(self, name: str, secs: typing.Union[int, float]):
        super(BaseWatch, self).__init__()
        self.fut = PendingFuture(self._post_event, secs)
        self.name: str = name

    async def _post_event(self):
        HABApp.core.EventBus.post_event(self.name, self.EVENT(self.name, self.fut.secs))

    async def __cancel_watch(self):
        self.fut.cancel()
        log.debug(f'Canceled {self.__class__.__name__} ({self.fut.secs}s) for {self.name}')

    def cancel(self):
        """Cancel the item watch"""
        super().cancel()
        asyncio.run_coroutine_threadsafe(self.__cancel_watch(), loop)

    def listen_event(self, callback: typing.Callable[[typing.Any], typing.Any]) -> 'HABApp.core.EventBusListener':
        """Listen to (only) the event that is emitted by this watcher"""
        ctx = HABApp.rule_ctx.get_rule_context()
        cb = HABApp.core.WrappedFunction(callback, name=ctx.get_callback_name(callback))
        listener = EventFilter(self.EVENT, seconds=self.fut.secs).create_event_listener(self.name, cb)
        return ctx.add_event_listener(listener)


class ItemNoUpdateWatch(BaseWatch):
    EVENT = ItemNoUpdateEvent


class ItemNoChangeWatch(BaseWatch):
    EVENT = ItemNoChangeEvent
