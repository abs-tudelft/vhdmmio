"""Module for counter-like subclasses of primitive fields."""

from .primitive import PrimitiveField
from ..logic_registry import field_logic
from ..utils import override, default

@field_logic('counter')
class CounterField(PrimitiveField):
    """Event counter field. This fulfills a similar role as flag fields, but
    instead of bit-setting, the operation is accumulation. This allows not only
    the occurance of one or more events to be registered, but also the amount.
    The clear operation is subtraction, so writing the previously read value
    will not clear any events that occurred between the read and the write."""

    def __init__(self, field_descriptor, dictionary):
        override(dictionary, {
            'bus_read':         'enabled',
            'bus_write':        'subtract',
        })

        default(dictionary, {
            'ctrl_increment':   'enabled',
            'hw_read':          'simple',
            'hw_write':         'disabled',
            'after_hw_write':   'nothing',
        })

        super().__init__(field_descriptor, dictionary)


@field_logic('volatile-counter')
class VolatileCounterField(PrimitiveField):
    """Same as a regular counter, but the value is cleared immediately when the
    register is read. This prevents the need for a write cycle, but requires
    read-volatility."""

    def __init__(self, field_descriptor, dictionary):
        override(dictionary, {
            'bus_read':         'enabled',
            'after_bus_read':   'clear',
        })

        default(dictionary, {
            'ctrl_increment':   'enabled',
            'hw_read':          'simple',
            'hw_write':         'disabled',
            'after_hw_write':   'nothing',
        })

        super().__init__(field_descriptor, dictionary)


@field_logic('internal-counter')
class InternalCounterField(PrimitiveField):
    """Same as a regular counter, but counts events on an internal instead of
    an external signal."""

    def __init__(self, field_descriptor, dictionary):
        override(dictionary, {
            'bus_read':         'enabled',
            'bus_write':        'subtract',
            'monitor_mode':     'increment',
        })

        default(dictionary, {
            'hw_read':          'disabled',
            'hw_write':         'disabled',
            'after_hw_write':   'nothing',
            'monitor_internal': field_descriptor.meta.name
        })

        super().__init__(field_descriptor, dictionary)


@field_logic('volatile-internal-counter')
class VolatileInternalCounterField(PrimitiveField):
    """Same as a regular internal counter, but the value is cleared immediately
    when the register is read. This prevents the need for a write cycle, but
    requires read-volatility."""

    def __init__(self, field_descriptor, dictionary):
        override(dictionary, {
            'bus_read':         'enabled',
            'after_bus_read':   'clear',
            'monitor_mode':     'increment',
        })

        default(dictionary, {
            'hw_read':          'disabled',
            'hw_write':         'disabled',
            'after_hw_write':   'nothing',
            'monitor_internal': field_descriptor.meta.name
        })

        super().__init__(field_descriptor, dictionary)


@field_logic('reverse-counter')
class ReverseCounterField(PrimitiveField):
    """Reverse form of a counter, where the counter is incremented by software
    and cleared by hardware."""

    def __init__(self, field_descriptor, dictionary):
        override(dictionary, {
            'bus_write':        'accumulate',
            'hw_read':          'simple',
            'ctrl_clear':       'enabled',
        })

        default(dictionary, {
            'bus_read':         'enabled',
        })

        super().__init__(field_descriptor, dictionary)
