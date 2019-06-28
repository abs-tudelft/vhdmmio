"""Module for AXC passthrough fields."""

from .logic import FieldLogic
from .logic_registry import field_logic
from .accesscaps import AccessCapabilities
from ..template import TemplateEngine

# TODO: placeholder code

_LOGIC_READ_REQUEST = """
"""

_LOGIC_READ_RESPONSE = """
"""

_LOGIC_WRITE_REQUEST = """
"""

_LOGIC_WRITE_RESPONSE = """
"""

@field_logic('axi')
class AXIField(FieldLogic):
    """AXI passthrough field."""

    def __init__(self, field_descriptor, dictionary):
        """Constructs an interrupt status/control field."""

        read_support = bool(dictionary.pop('read_support', True))
        write_support = bool(dictionary.pop('write_support', True))
        # TODO: interrupt support; requires new InternalInterrupt class that
        # doesn't generate an input signal but rather uses the interrupt from
        # the AXI-lite record. Also requires regfile to ask fields whether they
        # define interrupts.

        # Validate the field configuration.
        if field_descriptor.vector_width not in [32, 64]:
            raise ValueError('AXI field width must be 32 or 64 bits')
        if not read_support and not write_support:
            raise ValueError('cannot disable both read- and write support')

        # Determine the read/write capability fields.
        if read_support:
            read_caps = None
        else:
            read_caps = AccessCapabilities(volatile=True, can_block=True, can_defer=True)

        if write_support:
            write_caps = None
        else:
            write_caps = AccessCapabilities(volatile=True, can_block=True, can_defer=True)

        super().__init__(
            field_descriptor=field_descriptor,
            read_caps=read_caps,
            write_caps=write_caps)

    def to_dict(self, dictionary):
        """Returns a dictionary representation of this object."""
        super().to_dict(dictionary)
        if self.read_caps is None:
            dictionary['read-support'] = False
        if self.write_caps is None:
            dictionary['write-support'] = False

    def generate_vhdl(self, gen):
        """Generates the VHDL code for the associated field by updating the
        given `vhdl.Generator` object."""

        # TODO: placeholder code

        tple = TemplateEngine()
        tple['l'] = self

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
                both=expand(_LOGIC_READ_REQUEST),
                deferred=expand(_LOGIC_READ_RESPONSE))

        if self.write_caps is not None:
            gen.add_field_write_logic(
                self.field_descriptor,
                both=expand(_LOGIC_WRITE_REQUEST),
                deferred=expand(_LOGIC_WRITE_RESPONSE))
