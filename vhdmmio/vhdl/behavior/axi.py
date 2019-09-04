"""Submodule for AXI field behavior VHDL code generation."""

from ...template import TemplateEngine, preload_template
from ...core.behavior import AxiBehavior
from ..types import Axi4Lite, Record, Array, gather_defs
from .base import BehaviorCodeGen, behavior_code_gen

_TEMPLATE = preload_template('axi.template.vhd', '--')

@behavior_code_gen(AxiBehavior)
class AxiBehaviorCodeGen(BehaviorCodeGen):
    """Behavior code generator class for AXI fields."""

    def generate(self):
        """Code generator implementation."""

        bus_width = self.field_descriptor.base_bitrange.width

        tple = TemplateEngine()
        tple['b'] = self.behavior
        tple['fd'] = self.field_descriptor
        tple['width'] = bus_width

        # Generate I/Os.
        if self.behavior.cfg.bus_flatten:
            tple['awvalid'] = self.add_output('awvalid')
            tple['awready'] = self.add_input('awready')
            tple['awaddr'] = self.add_output('awaddr', 32)
            tple['awprot'] = self.add_output('awprot', 3)
            tple['wvalid'] = self.add_output('wvalid')
            tple['wready'] = self.add_input('wready')
            tple['wdata'] = self.add_output('wdata', bus_width)
            tple['wstrb'] = self.add_output('wstrb', bus_width // 8)
            tple['bvalid'] = self.add_input('bvalid')
            tple['bready'] = self.add_output('bready')
            tple['bresp'] = self.add_input('bresp', 2)
            tple['arvalid'] = self.add_output('arvalid')
            tple['arready'] = self.add_input('arready')
            tple['araddr'] = self.add_output('araddr', 32)
            tple['arprot'] = self.add_output('arprot', 3)
            tple['rvalid'] = self.add_input('rvalid')
            tple['rready'] = self.add_output('rready')
            tple['rdata'] = self.add_input('rdata', bus_width)
            tple['rresp'] = self.add_input('rresp', 2)
            tple['uirq'] = self.add_input('uirq')
        else:
            tple['m2s'] = self.add_output('o', typ=Axi4Lite('m2s', bus_width))
            tple['s2m'] = self.add_input('i', typ=Axi4Lite('s2m', bus_width))

        # Generate internal state.
        state_name = 'f_%s_r' % self.field_descriptor.name
        state_record = Record(state_name)
        components = []
        if self.behavior.bus.can_write() is not None:
            components.extend(['aw', 'w', 'b'])
        if self.behavior.bus.can_read():
            components.extend(['ar', 'r'])
        for component in components:
            state_record.append(component, Axi4Lite(component, bus_width))
        state_array = Array(state_name, state_record)
        state_decl, state_ob = state_array.make_variable(
            state_name, self.field_descriptor.width)
        tple['state'] = state_ob['$i$']
        state_defs = gather_defs(state_array)
        state_defs.append(state_decl + ';')
        self.add_declarations(private='\n'.join(state_defs))

        # Ignore some variables when expanding this template; they will be
        # expanded by the add_field_*_logic() functions.
        tple.passthrough('i', 'r_data', 'r_sub', 'w_data', 'w_strobe', 'w_sub')

        def expand(block):
            expanded = tple.apply_str_to_str(
                '%s\n\n$%s' % (_TEMPLATE, block), postprocess=False)
            if not expanded.strip():
                expanded = None
            return expanded

        self.add_interface_logic(expand('PRE'), expand('POST'))

        if self.behavior.bus.can_read():
            self.add_read_logic(both=expand('READ_REQ'), deferred=expand('READ_RESP'))

        if self.behavior.bus.can_write():
            self.add_write_logic(both=expand('WRITE_REQ'), deferred=expand('WRITE_RESP'))
