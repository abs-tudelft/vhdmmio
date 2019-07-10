"""Module for flag-like subclasses of primitive fields."""

from .primitive import PrimitiveField
from ..logic_registry import field_logic
from ..utils import override, default

@field_logic('flag')
class FlagField(PrimitiveField):
    """Field consisting of bit flags written by hardware and explicitly cleared
    by a write."""

    def __init__(self, field_descriptor, dictionary):
        override(dictionary, {
            'bus_read':         'enabled',
            'bus_write':        'bit-clear',
            'ctrl_bit_set':     'enabled',
        })

        default(dictionary, {
            'hw_read':          'simple',
        })

        super().__init__(field_descriptor, dictionary)


@field_logic('volatile-flag')
class VolatileFlagField(PrimitiveField):
    """Field consisting of bit flags written by hardware and implicitly cleared
    when read."""

    def __init__(self, field_descriptor, dictionary):
        override(dictionary, {
            'bus_read':         'enabled',
            'after_bus_read':   'clear',
            'ctrl_bit_set':     'enabled',
        })

        default(dictionary, {
            'hw_read':          'simple',
        })

        super().__init__(field_descriptor, dictionary)


@field_logic('internal-flag')
class InternalFlagField(PrimitiveField):
    """Same as a regular flag field, but monitors an internal instead of an
    external signal."""

    def __init__(self, field_descriptor, dictionary):
        override(dictionary, {
            'bus_read':         'enabled',
            'bus_write':        'bit-clear',
            'monitor_mode':     'bit-set',
        })

        default(dictionary, {
            'hw_read':          'disabled',
            'monitor_internal': field_descriptor.meta.name
        })

        super().__init__(field_descriptor, dictionary)


@field_logic('volatile-internal-flag')
class VolatileInternalFlagField(PrimitiveField):
    """Same as a regular volatile flag field, but monitors an internal instead
    of an external signal."""

    def __init__(self, field_descriptor, dictionary):
        override(dictionary, {
            'bus_read':         'enabled',
            'after_bus_read':   'clear',
            'monitor_mode':     'bit-set',
        })

        default(dictionary, {
            'hw_read':          'disabled',
            'monitor_internal': field_descriptor.meta.name
        })

        super().__init__(field_descriptor, dictionary)


@field_logic('reverse-flag')
class ReverseFlagField(PrimitiveField):
    """Reversed flag field: set by software, cleared by hardware."""

    def __init__(self, field_descriptor, dictionary):
        override(dictionary, {
            'bus_write':        'bit-set',
            'hw_read':          'simple',
            'ctrl_bit_clear':   'enabled',
        })

        default(dictionary, {
            'bus_read':         'enabled',
        })

        super().__init__(field_descriptor, dictionary)
