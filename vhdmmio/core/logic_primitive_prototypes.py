"""Module for primitive fields."""

from .logic_primitive import PrimitiveField
from .logic_registry import field_logic
from .utils import override, default

@field_logic('constant')
class ConstantField(PrimitiveField):
    """Read-only constant field. The constant is set in the register file
    description using the value key."""

    def __init__(self, field_descriptor, dictionary):
        value = dictionary.pop('value', None)
        if value is None:
            raise ValueError('missing value key')

        override(dictionary, {
            'bus_read':         'enabled',
            'after_bus_read':   'nothing',
            'bus_write':        'disabled',
            'after_bus_write':  'nothing',
            'hw_read':          'disabled',
            'hw_write':         'disabled',
            'after_hw_write':   'nothing',
            'reset':            value,
        })

        super().__init__(field_descriptor, dictionary)

        if self.ctrl:
            raise ValueError('constant fields do not support additional control signals')

    def to_dict(self, dictionary):
        """Returns a dictionary representation of this object."""
        super().to_dict(dictionary)
        del dictionary['reset']
        dictionary['value'] = self.reset


@field_logic('config')
class ConfigField(ConstantField):
    """Read-only constant field. The constant is set through a generic."""

    def __init__(self, field_descriptor, dictionary):
        override(dictionary, {'value': 'generic'})
        super().__init__(field_descriptor, dictionary)


@field_logic('status')
class StatusField(PrimitiveField):
    """Read-only field. The value is driven by an external signal."""

    def __init__(self, field_descriptor, dictionary):
        override(dictionary, {
            'bus_read':         'enabled',
            'after_bus_read':   'nothing',
            'bus_write':        'disabled',
            'after_bus_write':  'nothing',
            'hw_read':          'disabled',
            'hw_write':         'status',
            'after_hw_write':   'nothing',
            'reset':            None,
        })

        super().__init__(field_descriptor, dictionary)

        if self.ctrl:
            raise ValueError('status fields do not support additional control signals')


@field_logic('internal-status')
class InternalStatusField(PrimitiveField):
    """Read-only field. The value is driven by an internal signal, sharing its
    name with the field by default."""

    def __init__(self, field_descriptor, dictionary):
        override(dictionary, {
            'bus_read':         'enabled',
            'after_bus_read':   'nothing',
            'bus_write':        'disabled',
            'after_bus_write':  'nothing',
            'hw_read':          'disabled',
            'hw_write':         'disabled',
            'after_hw_write':   'nothing',
            'reset':            None,
            'monitor_mode':     'status',
        })

        default(dictionary, {
            'monitor_internal': field_descriptor.meta.name
        })

        super().__init__(field_descriptor, dictionary)

        if self.ctrl:
            raise ValueError('status fields do not support additional control signals')


@field_logic('latching')
class LatchingField(PrimitiveField):
    """Read-only field. The value is written by a stream-like interface."""

    def __init__(self, field_descriptor, dictionary):
        override(dictionary, {
            'bus_read':         'enabled',
            'hw_read':          'disabled',
            'hw_write':         'enabled',
        })

        default(dictionary, {
            'after_hw_write':   'validate'
        })

        super().__init__(field_descriptor, dictionary)


@field_logic('stream-to-mmio')
class StreamToMmioField(PrimitiveField):
    """Hardware to software stream. The stream is "popped" when the field is
    read, so it is write-once read-once; for write-once read-many use
    `latching` instead. By default, the read is blocked until a value is
    available."""

    def __init__(self, field_descriptor, dictionary):
        override(dictionary, {
            'after_bus_read':   'invalidate',
            'bus_write':        'disabled',
            'after_bus_write':  'nothing',
            'hw_read':          'handshake', # for the ready flag
            'hw_write':         'stream', # data; write enable = valid & ready
            'after_hw_write':   'validate',
        })

        default(dictionary, {
            'bus_read':         'valid-wait',
            'reset':            None,
        })

        super().__init__(field_descriptor, dictionary)


@field_logic('mmio-to-stream')
class MmioToStreamField(PrimitiveField):
    """Software to hardware stream. By default, writes are blocked while the
    field has not been popped by hardware yet. The valid bit of the internal
    register maps one-to-one to the stream valid signal, while the invalidate
    signal is connected to `ready`."""

    def __init__(self, field_descriptor, dictionary):
        override(dictionary, {
            'bus_read':         'disabled',
            'after_bus_read':   'nothing',
            'after_bus_write':  'validate',
            'hw_read':          'enabled', # for data and stream valid
            'hw_write':         'disabled',
            'after_hw_write':   'nothing',
            'ctrl_ready':       'enabled', # ready flag
        })

        default(dictionary, {
            'bus_write':        'invalid-wait',
            'reset':            None,
        })

        super().__init__(field_descriptor, dictionary)


@field_logic('control')
class ControlField(PrimitiveField):
    """Your standard control register; read-write by the bus and readable by
    hardware."""

    def __init__(self, field_descriptor, dictionary):
        default(dictionary, {
            'bus_read':         'enabled',
            'after_bus_read':   'nothing',
            'bus_write':        'masked',
            'after_bus_write':  'nothing',
            'hw_read':          'simple',
            'hw_write':         'disabled',
            'after_hw_write':   'nothing',
            'reset':            0,
        })

        super().__init__(field_descriptor, dictionary)


@field_logic('internal-control')
class InternalControlField(PrimitiveField):
    """Control register that drives an internal instead of external signal,
    sharing its name with the field by default."""

    def __init__(self, field_descriptor, dictionary):
        override(dictionary, {
            'bus_read':         'enabled',
            'after_bus_read':   'nothing',
            'bus_write':        'masked',
            'after_bus_write':  'nothing',
            'hw_read':          'simple',
            'hw_write':         'disabled',
            'after_hw_write':   'nothing',
            'reset':            0,
        })

        default(dictionary, {
            'drive_internal': field_descriptor.meta.name
        })

        super().__init__(field_descriptor, dictionary)

        if self.ctrl:
            raise ValueError('status fields do not support additional control signals')


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
