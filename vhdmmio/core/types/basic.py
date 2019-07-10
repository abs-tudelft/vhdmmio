"""Module for simple, commonly used subclasses of primitive fields."""

from .primitive import PrimitiveField
from ..logic_registry import field_logic
from ..utils import override, default

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
