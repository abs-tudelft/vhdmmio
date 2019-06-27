"""Module for primitive fields."""

from .logic import FieldLogic
from .logic_registry import field_logic
from .accesscaps import AccessCapabilities
from .utils import choice, switches, override, default
from ..template import TemplateEngine
from ..vhdl.types import (
    std_logic, std_logic_vector, SizedArray, Record, StdLogic, Array, gather_defs)

@field_logic('primitive')
class PrimitiveField(FieldLogic):
    """Basic field. Supports almost all register styles due to its high
    configurability."""

    def __init__(self, field_descriptor, dictionary):
        """Constructs a primitive field."""

        # Configures what happens when a read occurs.
        self._bus_read = choice(dictionary, 'bus_read', [
            'disabled',     # Read access is disabled.
            'error',        # Reads always return a slave error.
            'enabled',      # Normal read access to register, ignoring valid bit.
            'valid-wait',   # As above, but blocks until register is valid.
            'valid-only'])  # As above, but fails when register is not valid.

        # Configures what happens to the register after the read.
        self._after_bus_read = choice(dictionary, 'after_bus_read', [
            'nothing',      # No extra operation after read.
            'invalidate',   # Register is invalidated and cleared after read.
            'clear',        # Register is cleared after read, valid untouched.
            'increment',    # Register is incremented after read, valid untouched.
            'decrement'])   # Register is decremented after read, valid untouched.

        # Configures what happens when a write occurs.
        self._bus_write = choice(dictionary, 'bus_write', [
            'disabled',     # Write access is disabled.
            'error',        # Writes always return a slave error.
            'enabled',      # Normal write access to register. Masked bits are written 0.
            'invalid-wait', # As above, but blocks until register is invalid.
            'invalid-only', # As above, but fails when register is already valid.
            'masked',       # Write access respects strobe bits. Precludes after-bus-write.
            'accumulate',   # Write data is added to the register.
            'subtract',     # Write data is subtracted from the register.
            'bit-set',      # Bits that are written 1 are set in the register.
            'bit-clear',    # Bits that are written 1 are cleared in the register.
            'bit-toggle'])  # Bits that are written 1 are toggled in the register.

        # Configures what happens after a write occurs. Clear is special in
        # that it happens after the new value is pushed to the hardware read,
        # so it can be used to create a strobe register. The other operations
        # happen immediately after the write.
        self._after_bus_write = choice(dictionary, 'after_bus_write', [
            'nothing',      # No extra operation after write.
            'validate',     # Register is validated after write.
            'invalidate'])  # As above, but invalidated again one cycle later.

        # Configure hardware read port.
        self._hw_read = choice(dictionary, 'hw_read', [
            'disabled',     # No read port is generated.
            'simple',       # Only a simple data port is generated (no record).
            'enabled'])     # A record of the data and valid bit is generated.

        # Configure hardware write port.
        self._hw_write = choice(dictionary, 'hw_write', [
            'disabled',     # No write port is generated.
            'status',       # The register is constantly driven by a port and is always valid.
            'enabled',      # A record consisting of a write enable flag and data is generated.
            'invalid-only', # Like enabled, but the write only occurs when the register is invalid.
            'accumulate',   # Like enabled, but the data is accumulated instead of written.
            'subtract',     # Like enabled, but the data is subtracted instead of written.
            'set',          # Like enabled, but bits that are written 1 are set in the register.
            'reset',        # Like enabled, but bits that are written 1 are cleared in the register.
            'toggle'])      # Like enabled, but bits that are written 1 are toggled in the register.

        # Configures what happens after a hardware write occurs.
        self._after_hw_write = choice(dictionary, 'after_hw_write', [
            'nothing',      # No extra operation after write.
            'validate'])    # Register is automatically validated after write.

        # The following switches add an extra write port record.
        self._ctrl = switches(dictionary, 'ctrl', [
            'validate',     # Adds a strobe signal that validates the register.
            'invalidate',   # Adds a strobe signal that invalidates the register.
            'clear',        # Adds a strobe signal that clears the register (sets value to 0).
            'reset',        # Adds a strobe signal that works just like a global reset.
            'increment',    # Adds a strobe signal that increments the register.
            'decrement',    # Adds a strobe signal that decrements the register.
            'bit-set',      # Adds a vector of strobe signals that set bits in the register.
            'bit-clear',    # Adds a vector of strobe signals that reset bits in the register.
            'bit-toggle'])  # Adds a vector of strobe signals that toggle bits in the register.

        # Configures the reset value:
        #  - specify an integer to indicate that the field should have the
        #    given value after reset and be valid.
        #  - specify "generic" to generate a generic that specifies the initial
        #    value of the register.
        #  - specify null/None to indicate that the field should be invalid
        #    after reset.
        rst = dictionary.pop('reset', 0)
        if rst is not None and rst != 'generic' and not isinstance(rst, int):
            raise ValueError('reset must be an integer, "generic", or null')
        self._reset = rst

        # Validate the field configuration.
        if self._bus_read in ('disabled', 'error'):
            if self._after_bus_read != 'nothing':
                raise ValueError('bus read mode "%s" cannot be combined with a '
                                 'post-read operation' % self._bus_read)

        if self._bus_write in ('disabled', 'error', 'masked'):
            if self._after_bus_write != 'nothing':
                raise ValueError('bus write mode "%s" cannot be combined with a '
                                 'post-write operation' % self._bus_write)

        if self._hw_write in ('disabled', 'status'):
            if self._after_hw_write != 'nothing':
                raise ValueError('hardware write mode "%s" cannot be combined with a '
                                 'post-write operation' % self._hw_write)

        if self._hw_write == 'status':
            if self._ctrl:
                raise ValueError('status fields do not support additional control signals')
            if self._bus_write not in ('disabled', 'error'):
                raise ValueError('status fields cannot allow bus writes')

        # Determine the read/write capability fields.
        if self._bus_read == 'disabled':
            read_caps = None
        else:
            read_caps = AccessCapabilities(
                volatile=(self._after_bus_read != 'nothing'),
                can_block=(self._bus_read == 'valid-wait'))

        if self._bus_write == 'disabled':
            write_caps = None
        else:
            write_caps = AccessCapabilities(
                volatile=(self._after_bus_write != 'nothing'
                          or self._bus_write in ('accumulate', 'subtract', 'bit-toggle')),
                can_block=(self._bus_write == 'invalid-wait'))

        super().__init__(
            field_descriptor=field_descriptor,
            read_caps=read_caps,
            write_caps=write_caps)

        prefix = field_descriptor.meta.name.lower()

        tple = TemplateEngine()
        tple['l'] = self
        tple['f'] = self.field_descriptor
        tple['p'] = prefix
        tple['P'] = prefix.upper()
        width = self.field_descriptor.vector_width
        tple['xvw'] = width
        if width is None:
            width = 1
        tple['vw'] = width
        count = self.field_descriptor.vector_count
        tple['xvc'] = count
        if count is None:
            count = 1
        tple['vc'] = count

        if tple['xvw'] is None:
            self._value_type = std_logic
        else:
            self._value_type = SizedArray(prefix + '_value', std_logic_vector, tple['xvw'])

        self._state_type = Record(prefix + '_state')
        self._state_type.append('d', self._value_type)
        self._state_type.append('v', StdLogic(0))
        if tple['xvc'] is None:
            tple['state_variable'], self._state = self._state_type.make_variable(
                prefix + '_state')
        else:
            self._state_type = Array(prefix + '_state', self._state_type)
            tple['state_variable'], self._state = self._state_type.make_variable(
                prefix + '_state', prefix.upper() + '_COUNT')

        tple.append_block('PRIVATE_TYPES', gather_defs(self._state_type))

        self._tple = tple

    def to_dict(self, dictionary):
        """Returns a dictionary representation of this object."""
        super().to_dict(dictionary)
        dictionary['bus-read'] = self.bus_read
        dictionary['after-bus-read'] = self.after_bus_read
        dictionary['bus-write'] = self.bus_write
        dictionary['after-bus-write'] = self.after_bus_write
        dictionary['hw-read'] = self.hw_read
        dictionary['hw-write'] = self.hw_write
        dictionary['after-hw-write'] = self.after_hw_write
        dictionary['ctrl'] = list(self.ctrl)
        dictionary['reset'] = self.reset

    @property
    def bus_read(self):
        """Returns a string signifying the configured bus read operation."""
        return self._bus_read

    @property
    def after_bus_read(self):
        """Returns a string signifying the configured action after a bus
        read."""
        return self._after_bus_read

    @property
    def bus_write(self):
        """Returns a string signifying the configured bus write operation."""
        return self._bus_write

    @property
    def after_bus_write(self):
        """Returns a string signifying the configured action after a bus
        write."""
        return self._after_bus_write

    @property
    def hw_read(self):
        """Returns a string signifying the configured hardware read
        operation."""
        return self._hw_read

    @property
    def hw_write(self):
        """Returns a string signifying the configured hardware write
        operation."""
        return self._hw_write

    @property
    def after_hw_write(self):
        """Returns a string signifying the configured action after a hardware
        write."""
        return self._after_hw_write

    @property
    def ctrl(self):
        """Returns the set of ctrl options."""
        return set(self._ctrl)

    def get_ctrl(self, key):
        """Returns whether the given key is part of the ctrl options."""
        return key in self._ctrl

    @property
    def reset(self):
        """Returns the reset value for this register, which may be an int for
        a preconfigured value, the string `'generic'` to set the value with a
        generic, or `None` to reset the register to the invalid state."""
        return self._reset

    def generate_vhdl(self, generator):
        """Generates the VHDL code for the associated field by updating the
        given `vhdl.Generator` object."""
        # TODO


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
    """Read-only field. The value is driven by a signal."""

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
            'after-hw-write':   'validate'
        })

        super().__init__(field_descriptor, dictionary)


@field_logic('stream-to-mmio')
class StreamToMmioField(PrimitiveField):
    """Hardware to software stream. The stream is "popped" when the field is
    read, so it is write-once read-once; for write-once read-many use
    `latching` instead. By default, the read is blocked until a value is
    available. The valid bit of the internal register is used as the `!ready`
    signal for the stream, while the write-enable signal represents `valid`."""

    def __init__(self, field_descriptor, dictionary):
        override(dictionary, {
            'after_bus_read':   'invalidate',
            'bus_write':        'disabled',
            'after_bus_write':  'nothing',
            'hw_read':          'enabled', # for the register valid flag, serving as !ready
            'hw_write':         'invalid-only', # data; write enable = valid & ready
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
            'ctrl_invalidate':  'enabled', # ready flag
        })

        default(dictionary, {
            'bus_write':        'invalid-wait',
            'reset':            None,
        })

        super().__init__(field_descriptor, dictionary)


@field_logic('control')
class ControlField(PrimitiveField):
    """Your standard control register; read-write by the bus and readable by
    hardware.."""

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
    """Event counter field. With the default configuration, the register is
    incremented using a strobe control signal. The bus can then read the
    accumulated value. Values written to the register are subtracted from the
    counter, so a read-write cycle that writes the read value will "reset" the
    counter without losing any events that may be counted between the read and
    write. Decrement, accumulate, and readback signals can be optionally added
    when needed."""

    def __init__(self, field_descriptor, dictionary):
        override(dictionary, {
            'bus_read':         'enabled',
            'bus_write':        'subtract',
        })

        default(dictionary, {
            'ctrl_increment':   'enabled',
            'hw_read':          'disabled',
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
            'hw_read':          'disabled',
            'hw_write':         'disabled',
            'after_hw_write':   'nothing',
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
