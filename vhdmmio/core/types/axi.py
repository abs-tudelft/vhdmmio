"""Module for AXC passthrough fields."""

from ..logic import FieldLogic
from ..logic_registry import field_logic
from ..accesscaps import AccessCapabilities, NoOpMethod
from ...template import TemplateEngine, preload_template
from ...vhdl.types import Record, Array, Axi4Lite, gather_defs

_LOGIC_PRE = preload_template('axi-pre.template.vhd', '--')
_LOGIC_READ_REQUEST = preload_template('axi-read-req.template.vhd', '--')
_LOGIC_READ_RESPONSE = preload_template('axi-read-resp.template.vhd', '--')
_LOGIC_WRITE_REQUEST = preload_template('axi-write-req.template.vhd', '--')
_LOGIC_WRITE_RESPONSE = preload_template('axi-write-resp.template.vhd', '--')
_LOGIC_POST = preload_template('axi-post.template.vhd', '--')

@field_logic('axi')
class AXIField(FieldLogic):
    """AXI passthrough field."""

    def __init__(self, field_descriptor, dictionary):
        """Constructs an AXI passthrough field."""

        # Parse configuration options.
        read_support = bool(dictionary.pop('read_support', True))
        write_support = bool(dictionary.pop('write_support', True))
        interrupt_support = bool(dictionary.pop('interrupt_support', False))

        # Validate the field configuration.
        if field_descriptor.vector_width not in [32, 64]:
            raise ValueError('AXI field width must be 32 or 64 bits')
        if not read_support and not write_support:
            raise ValueError('cannot disable both read- and write support')

        # Register/connect internal interrupt signal.
        self._interrupt = None
        if interrupt_support:
            self._interrupt = self.field_descriptor.regfile.internal_signals.drive(
                self.field_descriptor,
                '%s_irq' % self.field_descriptor.meta.name,
                field_descriptor.vector_count)

        # Determine the read/write capability fields.
        if read_support:
            read_caps = AccessCapabilities(
                volatile=True, can_block=True, can_defer=True,
                no_op_method=NoOpMethod.NEVER, can_read_for_rmw=False)
        else:
            read_caps = None

        if write_support:
            write_caps = AccessCapabilities(
                volatile=True, can_block=True, can_defer=True,
                no_op_method=NoOpMethod.NEVER)
        else:
            write_caps = None

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
        if self._interrupt is not None:
            dictionary['interrupt-support'] = True

    @property
    def interrupt(self):
        """The internal signal that is connected to the incoming interrupt
        request flag, or `None` if the interrupt flag is ignored."""
        return self._interrupt

    def generate_vhdl(self, gen):
        """Generates the VHDL code for the associated field by updating the
        given `vhdl.Generator` object."""

        tple = TemplateEngine()
        tple['l'] = self
        tple['width'] = self.vector_width
        mask = (1 << self.field_descriptor.fields[0].bitrange.size) - 1
        tple['addr_mask'] = 'X"%08X"' % mask

        # Generate interface.
        tple['m2s'] = gen.add_field_port(
            self.field_descriptor, 'o', 'o', Axi4Lite('m2s', self.vector_width))
        tple['s2m'] = gen.add_field_port(
            self.field_descriptor, 'i', 'i', Axi4Lite('s2m', self.vector_width))

        # Generate internal state.
        state_name = 'f_%s_r' % self.field_descriptor.meta.name
        state_record = Record(state_name)
        components = []
        if self.write_caps is not None:
            components.extend(['aw', 'w', 'b'])
        if self.read_caps is not None:
            components.extend(['ar', 'r'])
        for component in components:
            state_record.append(component, Axi4Lite(component, self.vector_width))
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
                both=expand(_LOGIC_READ_REQUEST),
                deferred=expand(_LOGIC_READ_RESPONSE))

        if self.write_caps is not None:
            gen.add_field_write_logic(
                self.field_descriptor,
                both=expand(_LOGIC_WRITE_REQUEST),
                deferred=expand(_LOGIC_WRITE_RESPONSE))