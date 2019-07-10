"""Module for primitive fields."""

from ..logic import FieldLogic
from ..logic_registry import field_logic
from ..accesscaps import AccessCapabilities, NoOpMethod
from ..utils import choice, switches
from ...template import TemplateEngine, preload_template
from ...vhdl.types import std_logic, std_logic_vector, Record, Array, gather_defs

_LOGIC_PRE = preload_template('primitive-pre.template.vhd', '--')
_LOGIC_READ = preload_template('primitive-read.template.vhd', '--')
_LOGIC_WRITE = preload_template('primitive-write.template.vhd', '--')
_LOGIC_POST = preload_template('primitive-post.template.vhd', '--')

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
            'invalid',      # As above, but ignores the write when the register is valid.
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
            'enabled',      # A record of the data and valid bit is generated.
            'handshake'])   # A stream-to-mmio ready signal is generated.

        # Configure hardware write port.
        self._hw_write = choice(dictionary, 'hw_write', [
            'disabled',     # No write port is generated.
            'status',       # The register is constantly driven by a port and is always valid.
            'enabled',      # A record consisting of a write enable flag and data is generated.
            'stream',       # Like enabled, but the write only occurs when the register is invalid.
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
            'ready',        # As above, but renamed to "ready" for mmio-to-stream fields.
            'clear',        # Adds a strobe signal that clears the register (sets value to 0).
            'reset',        # Adds a strobe signal that works just like a global reset.
            'increment',    # Adds a strobe signal that increments the register.
            'decrement',    # Adds a strobe signal that decrements the register.
            'bit-set',      # Adds a vector of strobe signals that set bits in the register.
            'bit-clear',    # Adds a vector of strobe signals that reset bits in the register.
            'bit-toggle'])  # Adds a vector of strobe signals that toggle bits in the register.

        # Configures driving an internal signal with the value of this field.
        drive_internal = dictionary.pop('drive_internal', None)

        # Configures strobing an internal signal when a bus write occurs while
        # the stored value was already valid (this is an overflow condition for
        # MMIO to stream fields).
        overflow_internal = dictionary.pop('overflow_internal', None)

        # Configures strobing an internal signal when a bus read occurs while
        # the stored value is invalid (this is an underflow condition for
        # stream to MMIO fields).
        underflow_internal = dictionary.pop('underflow_internal', None)

        # Configures monitoring the value of an internal signal with this
        # field.
        monitor_internal = dictionary.pop('monitor_internal', None)

        # Configures the way the internal monitor signal is monitored.
        self._monitor_mode = choice(dictionary, 'monitor_mode', [
            'status',       # The vector-sized internal signal is constantly driven.
            'bit-set',      # The vector-sized internal signal bit-sets the register.
            'increment'])   # The count-sized internal signal increments the register.

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

        if monitor_internal is not None and self._monitor_mode == 'status':
            if self._ctrl:
                raise ValueError('status fields do not support additional control signals')
            if self._bus_write not in ('disabled', 'error'):
                raise ValueError('status fields cannot allow bus writes')
            if self._hw_write != 'disabled':
                raise ValueError('cannot monitor both internal and external signal')

        if self._hw_write == 'stream':
            if self._hw_read == 'enabled':
                raise ValueError('cannot combine hw-write=stream with hw-read=enabled '
                                 '(name conflict for "valid" and "data" signals)')
            if self._hw_read == 'simple':
                raise ValueError('cannot combine hw-write=stream with hw-read=simple '
                                 '(name conflict for "data" signal)')

        if self._hw_read == 'handshake' and 'ready' in self._ctrl:
            raise ValueError('cannot combine hw-read=handshake with ctrl-ready=enabled '
                             '(name conflict for "ready" signal)')

        self._drive_internal = None
        if drive_internal is not None:
            if field_descriptor.vector_count is not None:
                raise ValueError('cannot drive internal signal with repeated field')
            self._drive_internal = field_descriptor.regfile.internal_signals.drive(
                field_descriptor, drive_internal, field_descriptor.vector_width)

        self._overflow_internal = None
        if overflow_internal is not None:
            self._overflow_internal = field_descriptor.regfile.internal_signals.strobe(
                field_descriptor, overflow_internal, field_descriptor.vector_count)

        self._underflow_internal = None
        if underflow_internal is not None:
            self._underflow_internal = field_descriptor.regfile.internal_signals.strobe(
                field_descriptor, underflow_internal, field_descriptor.vector_count)

        self._monitor_internal = None
        if monitor_internal is not None:
            if self._monitor_mode == 'increment':
                width = field_descriptor.vector_count
            else:
                width = field_descriptor.vector_width
                if field_descriptor.vector_count is not None:
                    raise ValueError('cannot monitor internal signal with repeated field')
            self._monitor_internal = field_descriptor.regfile.internal_signals.use(
                field_descriptor, monitor_internal, width)

        # Determine the read/write capability fields.
        if self._bus_read == 'disabled':
            read_caps = None
        else:
            volatile = False
            can_block = self._bus_read == 'valid-wait'
            no_op_method = NoOpMethod.ALWAYS
            can_read_for_rmw = self._bus_read != 'error'

            if self._after_bus_read != 'nothing':
                volatile = True
                no_op_method = NoOpMethod.NEVER

            read_caps = AccessCapabilities(
                volatile=volatile,
                can_block=can_block,
                no_op_method=no_op_method,
                can_read_for_rmw=can_read_for_rmw)

        if self._bus_write == 'disabled':
            write_caps = None
        else:
            volatile = self._bus_write in ('accumulate', 'subtract', 'bit-toggle')
            can_block = self._bus_write == 'invalid-wait'
            no_op_method = NoOpMethod.WRITE_ZERO

            if self._bus_write == 'error':
                no_op_method = NoOpMethod.ALWAYS
            elif self._bus_write == 'masked':
                no_op_method = NoOpMethod.WRITE_CURRENT_OR_MASK
            elif self._bus_write in ('enabled', 'invalid-wait', 'invalid-only'):
                no_op_method = NoOpMethod.WRITE_CURRENT

            if self._after_bus_write != 'nothing':
                volatile = True
                no_op_method = NoOpMethod.NEVER

            write_caps = AccessCapabilities(
                volatile=volatile,
                can_block=can_block,
                no_op_method=no_op_method)

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
        if self.drive_internal:
            dictionary['drive-internal'] = self.drive_internal.name
        if self.overflow_internal:
            dictionary['overflow-internal'] = self.overflow_internal.name
        if self.underflow_internal:
            dictionary['underflow-internal'] = self.underflow_internal.name
        if self.monitor_internal:
            dictionary['monitor-internal'] = self.monitor_internal.name
            dictionary['monitor-mode'] = self.monitor_mode

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

    @property
    def drive_internal(self):
        """Returns the internal signal that is driven by this field, if any.
        Returns `None` if there is no such signal."""
        return self._drive_internal

    @property
    def overflow_internal(self):
        """Returns the internal signal that is strobed when this field is
        written while the internal register is already valid, if any. Returns
        `None` if there is no such signal."""
        return self._overflow_internal

    @property
    def underflow_internal(self):
        """Returns the internal signal that is strobed when this field is
        read while the internal register is invalid, if any. Returns `None` if
        there is no such signal."""
        return self._underflow_internal

    @property
    def monitor_internal(self):
        """Returns the internal signal that is monitored by this field, if any.
        Returns `None` if there is no such signal."""
        return self._monitor_internal

    @property
    def monitor_mode(self):
        """The mode with which the `monitor_internal` signal is monitored."""
        return self._monitor_mode

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
            if self.hw_write == 'stream':
                add_input('data', self.vector_width)
                add_input('valid')
            else:
                add_input('write_data', self.vector_width)
                if self.hw_write != 'status':
                    add_input('write_enable')
        ctrl_signals = [
            'lock', 'validate', 'invalidate', 'ready', 'clear', 'reset', 'increment', 'decrement']
        for ctrl_signal in ctrl_signals:
            if ctrl_signal in self._ctrl:
                add_input(ctrl_signal)
        bit_signals = ['bit_set', 'bit_clear', 'bit_toggle']
        for bit_signal in bit_signals:
            if bit_signal.replace('_', '-') in self._ctrl:
                add_input(bit_signal, self.vector_width)
        if self.hw_read in ('simple', 'enabled'):
            add_output('data', self.vector_width)
            if self.hw_read != 'simple':
                add_output('valid')
        if self.hw_read == 'handshake':
            add_output('ready')
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
