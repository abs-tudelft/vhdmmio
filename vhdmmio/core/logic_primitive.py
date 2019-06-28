"""Module for primitive fields."""

from .logic import FieldLogic
from .logic_registry import field_logic
from .accesscaps import AccessCapabilities
from .utils import choice, switches, override, default
from ..template import TemplateEngine
from ..vhdl.types import std_logic, std_logic_vector, Record, Array, gather_defs

_LOGIC_PRE = """
$if l.get_ctrl('invalidate')
@ Handle invalidation control input.
if $invalidate[i]$ = '1' then
$if vec
  $state[i].d$@:= (others => '0');
$else
  $state[i].d$@:= '0';
$endif
  $state[i].v$@:= '0';
end if;
$endif

$if l.get_ctrl('clear')
@ Handle clear control input.
if $clear[i]$ = '1' then
$if vec
  $state[i].d$@:= (others => '0');
$else
  $state[i].d$@:= '0';
$endif
end if;
$endif

$if l.after_bus_write == 'invalidate'
@ Handle post-write invalidation one cycle after the write occurs.
if $state[i].inval$ = '1' then
$if vec
  $state[i].d$@:= (others => '0');
$else
  $state[i].d$@:= '0';
$endif
  $state[i].v$@:= '0';
end if;
$state[i].inval$@:= '0';
$endif
"""

_LOGIC_READ = """
$block AFTER_READ
$if l.after_bus_read != 'nothing'
@ Handle post-read operation: $l.after_bus_read$.
$endif
$if l.after_bus_read in ['invalidate', 'clear']
$if vec
$state[i].d$@:= (others => '0');
$else
$state[i].d$@:= '0';
$endif
$endif
$if l.after_bus_read == 'invalidate'
$state[i].v$@:= '0';
$endif
$if l.after_bus_read == 'increment'
$if vec
$state[i].d$@:= std_logic_vector(unsigned($state[i].d$) + 1);
$else
$state[i].d$@:= not $state[i].d$;
$endif
$endif
$if l.after_bus_read == 'decrement'
$if vec
$state[i].d$@:= std_logic_vector(unsigned($state[i].d$) - 1);
$else
$state[i].d$@:= not $state[i].d$;
$endif
$endif
$endblock

$if l.bus_read != 'disabled'
@ Read mode: $l.bus_read$.
$endif
$if l.bus_read == 'error'
r_nack@:= true;
$endif
$if l.bus_read in ['enabled', 'valid-wait', 'valid-only']
$r_data$@:= $state[i].d$;
$if l.bus_read in ['valid-wait', 'valid-only']
if $state[i].v$ = '1' then
  r_ack@:= true;
$ AFTER_READ
else
$if l.bus_read in ['valid-wait']
  r_block@:= true;
$else
  r_nack@:= true;
$endif
end if;
$else
r_ack@:= true;
$AFTER_READ
$endif
$endif
"""

_LOGIC_WRITE = """
$block AFTER_WRITE
$if l.after_bus_write != 'nothing'
@ Handle post-write operation: $l.after_bus_write$.
$endif
$if l.after_bus_write == 'validate'
$state[i].v$@:= '1';
$endif
$if l.after_bus_write == 'invalidate'
$state[i].v$@:= '1';
$state[i].inval$@:= '1';
$endif
$endblock

$block HANDLE_WRITE
$if l.bus_write == 'error'
w_nack@:= true;
$endif
$if l.bus_write == 'invalid-wait'
if $state[i].v$ = '1' then
  w_block@:= true;
else
  $state[i].d$@:= $w_data$;
  w_ack@:= true;
$ AFTER_WRITE
end if;
$endif
$if l.bus_write == 'invalid-only'
if $state[i].v$ = '1' then
  w_nack@:= true;
else
  $state[i].d$@:= $w_data$;
  w_ack@:= true;
$ AFTER_WRITE
end if;
$endif
$if l.bus_write == 'enabled'
$state[i].d$@:= $w_data$;
w_ack@:= true;
$AFTER_WRITE
$endif
$if l.bus_write == 'masked'
$state[i].d$@:= ($state[i].d$ and not $w_strobe$)@or $w_data$;
w_ack@:= true;
$AFTER_WRITE
$endif
$if l.bus_write == 'accumulate'
$if vec
$state[i].d$@:= std_logic_vector(unsigned($state[i].d$)@+ unsigned($w_data$));
$else
$state[i].d$@:= $state[i].d$@xor $w_data$;
$endif
w_ack@:= true;
$AFTER_WRITE
$endif
$if l.bus_write == 'subtract'
$if vec
$state[i].d$@:= std_logic_vector(unsigned($state[i].d$)@- unsigned($w_data$));
$else
$state[i].d$@:= $state[i].d$@xor $w_data$;
$endif
w_ack@:= true;
$AFTER_WRITE
$endif
$if l.bus_write == 'bit-set'
$state[i].d$@:= $state[i].d$@or $w_data$;
w_ack@:= true;
$AFTER_WRITE
$endif
$if l.bus_write == 'bit-clear'
$state[i].d$@:= $state[i].d$@and not $w_data$;
w_ack@:= true;
$AFTER_WRITE
$endif
$if l.bus_write == 'bit-toggle'
$state[i].d$@:= $state[i].d$@xor $w_data$;
w_ack@:= true;
$AFTER_WRITE
$endif
$endblock

$if l.bus_write != 'disabled'
@ Write mode: $l.bus_write$.
$if l.get_ctrl('lock')
if $lock[i]$ = '0' then
$ HANDLE_WRITE
end if;
$else
$HANDLE_WRITE
$endif
$endif
"""

_LOGIC_POST = """
$if l.hw_write not in 'disabled'
@ Handle hardware write for field $l.field_descriptor.meta.name$: $l.hw_write$.
$if l.after_hw_write != 'nothing'
@ Also handle post-write operation: $l.after_hw_write$.
$endif
$if l.hw_write == 'status'
$state[i].d$@:= $reset_data if isinstance(reset_data, str) else reset_data[i]$;
$state[i].v$@:= '1';
$else
$if l.hw_write == 'invalid-only'
if $write_enable[i]$ = '1' and $state[i].v$ = '0' then
$else
if $write_enable[i]$ = '1' then
$endif
$if l.hw_write in ['enabled', 'invalid-only']
  $state[i].d$@:= $write_data[i]$;
$endif
$if l.hw_write == 'accumulate'
$if vec
  $state[i].d$@:= std_logic_vector(unsigned($state[i].d$)@+ unsigned($write_data[i]$));
$else
  $state[i].d$@:= $state[i].d$@xor $write_data[i]$;
$endif
$endif
$if l.hw_write == 'subtract'
$if vec
  $state[i].d$@:= std_logic_vector(unsigned($state[i].d$)@- unsigned($write_data[i]$));
$else
  $state[i].d$@:= $state[i].d$@xor $write_data[i]$;
$endif
$endif
$if l.hw_write == 'set'
  $state[i].d$@:= $state[i].d$@or $write_data[i]$;
$endif
$if l.hw_write == 'reset'
  $state[i].d$@:= $state[i].d$@and not $write_data[i]$;
$endif
$if l.hw_write == 'toggle'
  $state[i].d$@:= $state[i].d$@xor $write_data[i]$;
$endif
$if l.after_hw_write == 'validate'
  $state[i].v$@:= '1';
$endif
end if;
$endif
$endif

$if l.get_ctrl('validate')
@ Handle validation control input.
if $validate[i]$ = '1' then
  $state[i].v$@:= '1';
end if;
$endif

$if l.get_ctrl('increment')
@ Handle increment control input.
if $increment[i]$ = '1' then
$if vec
  $state[i].d$@:= std_logic_vector(unsigned($state[i].d$) + 1);
$else
  $state[i].d$@:= not $state[i].d$;
$endif
end if;
$endif

$if l.get_ctrl('decrement')
@ Handle decrement control input.
if $decrement[i]$ = '1' then
$if vec
  $state[i].d$@:= std_logic_vector(unsigned($state[i].d$) - 1);
$else
  $state[i].d$@:= not $state[i].d$;
$endif
end if;
$endif

$if l.get_ctrl('bit_set')
@ Handle bit set control input.
$state[i].d$@:= $state[i].d$@or $bit_set[i]$;
$endif

$if l.get_ctrl('bit_clear')
@ Handle bit clear control input.
$state[i].d$@:= $state[i].d$@and not $bit_clear[i]$;
$endif

$if l.get_ctrl('bit_toggle')
@ Handle bit toggle control input.
$state[i].d$@:= $state[i].d$@and xor $bit_toggle[i]$;
$endif

$if l.hw_write != 'status'
@ Handle reset for field $l.field_descriptor.meta.name$.
$if l.get_ctrl('reset')
@ This includes the optional per-field reset control signal.
if reset = '1' or $reset[i]$ = '1' then
$else
if reset = '1' then
$endif
  $state[i].d$@:= $reset_data if isinstance(reset_data, str) else reset_data[i]$;
  $state[i].v$@:= $reset_valid$;
$if l.after_bus_write == 'invalidate'
  $state[i].inval$@:= '0';
$endif
end if;
$endif

$if l.hw_read != 'disabled'
@ Assign the read outputs for field $l.field_descriptor.meta.name$.
$data[i]$ <= $state[i].d$;
$if l.hw_read == 'enabled'
$valid[i]$ <= $state[i].v$;
$endif
$endif
"""

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
            'lock',         # When asserted, disables the bus write logic.
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
        return self._ctrl

    def get_ctrl(self, key):
        """Returns whether the given key is part of the ctrl options."""
        return key in self._ctrl

    @property
    def reset(self):
        """Returns the reset value for this register, which may be an int for
        a preconfigured value, the string `'generic'` to set the value with a
        generic, or `None` to reset the register to the invalid state."""
        return self._reset

    def generate_vhdl(self, gen):
        """Generates the VHDL code for the associated field by updating the
        given `vhdl.Generator` object."""

        tple = TemplateEngine()
        tple['l'] = self
        tple['vec'] = self.field_descriptor.vector_width is not None

        def add_input(name, width=None):
            tple[name] = gen.add_field_port(self.field_descriptor, name, 'i', None, width)
        def add_output(name, width=None):
            tple[name] = gen.add_field_port(self.field_descriptor, name, 'o', None, width)
        def add_generic(name, typ=None, width=None):
            tple[name] = gen.add_field_generic(self.field_descriptor, name, typ, width)

        # Generate interface.
        if self.hw_write != 'disabled':
            add_input('write_data', self.vector_width)
            if self.hw_write != 'status':
                add_input('write_enable')
        ctrl_signals = [
            'lock', 'validate', 'invalidate', 'clear', 'reset', 'increment', 'decrement']
        for ctrl_signal in ctrl_signals:
            if ctrl_signal in self._ctrl:
                add_input(ctrl_signal)
        bit_signals = ['bit_set', 'bit_clear', 'bit_toggle']
        for bit_signal in bit_signals:
            if bit_signal.replace('_', '-') in self._ctrl:
                add_input(bit_signal, self.vector_width)
        if self.hw_read != 'disabled':
            add_output('data', self.vector_width)
            if self.hw_read != 'simple':
                add_output('valid')
        if self.reset == 'generic':
            add_generic('reset_data', None, self.vector_width)
            tple['reset_valid'] = "'1'"
        elif self.reset is None:
            if self.vector_width is None:
                tple['reset_data'] = "'0'"
            else:
                tple['reset_data'] = "(others => '0')"
            tple['reset_valid'] = "'0'"
        else:
            if self.vector_width is None:
                if self.reset:
                    tple['reset_data'] = "'1'"
                else:
                    tple['reset_data'] = "'0'"
            else:
                fmt = ('"{:0%db}"' % self.vector_width)
                tple['reset_data'] = fmt.format(self.reset & ((1 << self.vector_width) - 1))
            tple['reset_valid'] = "'1'"

        # Generate internal state.
        state_name = 'f_%s_r' % self.field_descriptor.meta.name
        state_record = Record(state_name)
        if self.vector_width is not None:
            state_record.append('d', std_logic_vector, self.vector_width)
        else:
            state_record.append('d', std_logic)
        state_record.append('v', std_logic)
        if self.after_bus_write == 'invalidate':
            state_record.append('inval', std_logic)
        state_array = Array(state_name, state_record)
        count = 1
        if self.vector_count is not None:
            count = self.vector_count
        state_decl, state_ob = state_array.make_variable(state_name, count)
        tple['state'] = state_ob
        state_defs = gather_defs(state_array)
        state_defs.append(state_decl + ';')
        gen.add_field_declarations(self.field_descriptor, private='\n'.join(state_defs))

        # Ignore some variables when expanding this template; they will be
        # expanded by the add_field_*_logic() functions.
        tple.passthrough('i', 'r_data', 'w_data', 'w_strobe')

        def expand(template):
            expanded = tple.apply_str_to_str(template, postprocess=False)
            if not expanded.strip():
                expanded = None
            return expanded

        gen.add_field_interface_logic(
            self.field_descriptor,
            expand(_LOGIC_PRE),
            expand(_LOGIC_POST))

        if self.read_caps is not None:
            gen.add_field_read_logic(
                self.field_descriptor,
                expand(_LOGIC_READ))

        if self.write_caps is not None:
            gen.add_field_write_logic(
                self.field_descriptor,
                expand(_LOGIC_WRITE))


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
            'after_hw_write':   'validate'
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
