from HABApp.core.events.filter import ValueChangeEventFilter, ValueUpdateEventFilter
from . import MqttValueChangeEvent, MqttValueUpdateEvent


class MqttValueUpdateEventFilter(ValueUpdateEventFilter):
    _EVENT_TYPE = MqttValueUpdateEvent


class MqttValueChangeEventFilter(ValueChangeEventFilter):
    _EVENT_TYPE = MqttValueChangeEvent
