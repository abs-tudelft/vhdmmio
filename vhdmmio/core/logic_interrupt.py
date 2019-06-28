"""Module for interrupt fields."""

from .logic import FieldLogic
from .logic_registry import field_logic
from .accesscaps import AccessCapabilities
from .utils import choice, override, default
from ..template import TemplateEngine

_LOGIC_READ = """
@ Read mode: $l.read$.
$r_data$ := $v$;
$if l.read == 'clear'
$v$ := '0';
$endif
r_ack := true;
"""

_LOGIC_WRITE = """
@ Write mode: $l.write$.
$if l.write == 'enabled'
$v$ := ($v$ and not $w_strobe$) or $w_data$;
$endif
$if l.write == 'clear'
$v$ := $v$ and not $w_data$;
$endif
$if l.write == 'set'
$v$ := $v$ or $w_data$;
$endif
"""

@field_logic('interrupt')
class InterruptField(FieldLogic):
    """Interrupt status/control field."""

    def __init__(self, field_descriptor, dictionary):
        """Constructs an interrupt status/control field."""

        # Selects the interrupt that this field is operating on.
        self._irq_name = dictionary.pop('interrupt', None)

        # Configures which signal of the interrupt logic this field operates
        # on.
        self._function = choice(dictionary, 'function', [
            'raw',          # Status-only view of the raw interrupt requests.
            'enable',       # Connects to the enable register (whether requests are passed through).
            'flag',         # Connects to the flag register (whether the interrupt is pending).
            'unmask',       # Connects to the unmask register (whether flags are passed through).
            'masked'])      # Status-only view of the flag register masked by the unmask register.

        # Configures the read behavior of the field.
        self._read = choice(dictionary, 'read', [
            'disabled',     # The field is write-only.
            'enabled',      # Read access is enabled.
            'clear'])       # Read access is enabled, and the act of reading clears the register.

        # Configures what happens when a write occurs.
        self._write = choice(dictionary, 'write', [
            'disabled',     # The field is read-only.
            'enabled',      # Writes operate on the register in the usual way.
            'clear',        # Writing one clears the register.
            'set'])         # Writing one sets the register.

        # Validate the field configuration.
        if self._irq_name is None:
            raise ValueError('missing name of the interrupt to connect to')

        if self._read == 'disabled' and self._write == 'disabled':
            raise ValueError('field is no-operation; specify a read operation '
                             'or a write operation')

        if self._function == 'raw' and self._write != 'disabled':
            raise ValueError('raw interrupt status can not be written')

        if self._function == 'masked' and self._write != 'disabled':
            raise ValueError('masked interrupt status can not be written')

        if self._read == 'clear' and self._function != 'flag':
            raise ValueError('clear-on-read is only sensible for flag fields')

        if field_descriptor.vector_width is not None:
            raise ValueError('interrupt fields cannot be vectors, use '
                             'repeat instead')

        # Determine the read/write capability fields.
        if self._read == 'disabled':
            read_caps = None
        else:
            read_caps = AccessCapabilities(volatile=self._read == 'clear')

        if self._write == 'disabled':
            write_caps = None
        else:
            write_caps = AccessCapabilities()

        super().__init__(
            field_descriptor=field_descriptor,
            read_caps=read_caps,
            write_caps=write_caps)

        self._interrupt = None

    def to_dict(self, dictionary):
        """Returns a dictionary representation of this object."""
        super().to_dict(dictionary)
        dictionary['interrupt'] = self.irq_name
        dictionary['function'] = self.function
        if self.read != 'disabled':
            dictionary['read'] = self.read
        if self.write != 'disabled':
            dictionary['write'] = self.write

    @property
    def irq_name(self):
        """Returns the name of the interrupt that we're bound to."""
        return self._irq_name

    @property
    def interrupt(self):
        """Returns the `Interrupt` object that we're bound to."""
        assert self._interrupt is not None
        return self._interrupt

    @interrupt.setter
    def interrupt(self, interrupt):
        assert self._interrupt is None

        # Make sure that the interrupt and field have the same size.
        if interrupt.width is not self.field_descriptor.vector_count:
            raise ValueError(
                'size mismatch between field %s (%s) and associated interrupt '
                '%s (%s)' % (
                    self.field_descriptor.meta.name,
                    self.field_descriptor.vector_count,
                    interrupt.meta.name,
                    interrupt.width))

        # Register the functionality of this field with the interrupt.
        if self.write != 'disabled':
            if self.function == 'enable':
                interrupt.register_enable()
            if self.function == 'unmask':
                interrupt.register_unmask()
        if self.function == 'flag':
            if self.write in ['enabled', 'clear'] or self.read == 'clear':
                interrupt.register_clear()
            if self.write in ['enabled', 'set']:
                interrupt.register_pend()

        self._interrupt = interrupt

    @property
    def offset(self):
        """Returns the bit offset for this field within the interrupt
        variables."""
        return self.interrupt.low

    @property
    def function(self):
        """Returns a string signifying which interrupt control signal we're
        associated with."""
        return self._function

    @property
    def read(self):
        """Returns a string signifying the configured bus read operation."""
        return self._read

    @property
    def write(self):
        """Returns a string signifying the configured bus write operation."""
        return self._write

    def generate_vhdl(self, gen):
        """Generates the VHDL code for the associated field by updating the
        given `vhdl.Generator` object."""

        tple = TemplateEngine()
        tple['l'] = self
        tple['v'] = {
            'raw':    'i_req{0}',
            'enable': 'i_enab{0}',
            'flag':   'i_flag{0}',
            'unmask': 'i_umsk{0}',
            'masked': '(i_flag{0} and i_umsk{0})',
        }[self.function].format(
            '($i + {0} if isinstance(i, int) else "%s + {0}" % i$)'
            .format(self.offset))

        # Ignore some variables when expanding this template; they will be
        # expanded by the add_field_*_logic() functions.
        tple.passthrough('i', 'r_data', 'w_data', 'w_strobe')

        def expand(template):
            expanded = tple.apply_str_to_str(template, postprocess=False)
            if not expanded.strip():
                expanded = None
            return expanded

        if self.read_caps is not None:
            gen.add_field_read_logic(
                self.field_descriptor,
                expand(_LOGIC_READ))

        if self.write_caps is not None:
            gen.add_field_write_logic(
                self.field_descriptor,
                expand(_LOGIC_WRITE))


@field_logic('interrupt-flag-cow')
class InterruptFlagCOWField(InterruptField):
    """Interrupt flag clear-on-write field. Read mode can optionally be
    disabled."""

    def __init__(self, field_descriptor, dictionary):
        override(dictionary, {
            'function': 'flag',
            'write':    'clear',
        })

        default(dictionary, {
            'read':     'enabled',
        })

        super().__init__(field_descriptor, dictionary)

@field_logic('interrupt-flag-cor')
class InterruptFlagCORField(InterruptField):
    """Interrupt flag clear-on-read field."""

    def __init__(self, field_descriptor, dictionary):
        override(dictionary, {
            'function': 'flag',
            'read':     'clear',
        })

        super().__init__(field_descriptor, dictionary)

@field_logic('interrupt-flag')
class InterruptFlagField(InterruptField):
    """Read-only interrupt flag field."""

    def __init__(self, field_descriptor, dictionary):
        override(dictionary, {
            'function': 'flag',
            'write':    'disabled',
            'read':     'enabled',
        })

        super().__init__(field_descriptor, dictionary)

@field_logic('interrupt-pend')
class InterruptPendField(InterruptField):
    """Software-pend field. Read mode can optionally be disabled."""

    def __init__(self, field_descriptor, dictionary):
        override(dictionary, {
            'function': 'flag',
            'write':    'set',
        })

        default(dictionary, {
            'read':     'enabled',
        })

        super().__init__(field_descriptor, dictionary)

@field_logic('interrupt-enable')
class InterruptEnableField(InterruptField):
    """Field that controls the enable register for an interrupt. Defaults to
    read-write."""

    def __init__(self, field_descriptor, dictionary):
        override(dictionary, {
            'function': 'enable',
        })

        default(dictionary, {
            'write':    'enabled',
            'read':     'enabled',
        })

        super().__init__(field_descriptor, dictionary)

@field_logic('interrupt-unmask')
class InterruptUnmaskField(InterruptField):
    """Field that controls the unmask register for an interrupt. Defaults to
    read-write."""

    def __init__(self, field_descriptor, dictionary):
        override(dictionary, {
            'function': 'unmask',
        })

        default(dictionary, {
            'write':    'enabled',
            'read':     'enabled',
        })

        super().__init__(field_descriptor, dictionary)

@field_logic('interrupt-status')
class InterruptStatusField(InterruptField):
    """Field that allows the masked interrupt flag to be read."""

    def __init__(self, field_descriptor, dictionary):
        override(dictionary, {
            'function': 'masked',
            'read':     'enabled',
            'write':    'disabled',
        })

        super().__init__(field_descriptor, dictionary)

@field_logic('interrupt-raw')
class InterruptRawField(InterruptField):
    """Field that allows the raw, incoming interrupt status to be read. Note
    that normally you want to read the flag register instead; use
    interrupt-flag and/or interrupt-status for that."""

    def __init__(self, field_descriptor, dictionary):
        override(dictionary, {
            'function': 'raw',
            'read':     'enabled',
            'write':    'disabled',
        })

        super().__init__(field_descriptor, dictionary)
