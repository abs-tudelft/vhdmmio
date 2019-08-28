"""Submodule for primitive field behavior VHDL code generation."""

from ...template import TemplateEngine, preload_template
from ...core.behavior import PrimitiveBehavior
from ..types import std_logic, std_logic_vector, Record, Array, gather_defs
from .base import BehaviorCodeGen, behavior_code_gen

_TEMPLATE = preload_template('primitive.template.vhd', '--')

@behavior_code_gen(PrimitiveBehavior)
class PrimitiveBehaviorCodeGen(BehaviorCodeGen):
    """Behavior code generator class for primitive fields."""

    def generate(self):
        """Code generator implementation."""

        field_shape = self.field_descriptor.base_bitrange.shape

        accum = (
            self.behavior.cfg.hw_write in ('accumulate', 'subtract')
            or self.behavior.cfg.bus_write in ('accumulate', 'subtract')
            or self.behavior.cfg.after_bus_read in ('increment', 'decrement')
            or self.behavior.cfg.ctrl_increment
            or self.behavior.cfg.ctrl_decrement
            or self.behavior.cfg.monitor_mode == 'increment')

        tple = TemplateEngine()
        tple['b'] = self.behavior
        tple['fd'] = self.field_descriptor
        tple['vec'] = field_shape is not None
        tple['accum'] = accum
        cfg = self.behavior.cfg

        # Shorthand functions for adding interface signals.
        def add_input(name, width=None):
            tple[name] = self.add_input(name, width)
        def add_output(name, width=None):
            tple[name] = self.add_output(name, width)
        def add_generic(name, typ=None, width=None):
            tple[name] = self.add_generic(name, typ=typ, count=width)

        # Generate read/mmio-to-stream interface in canonical signal order.
        if cfg.hw_read not in ('disabled', 'handshake', 'simple'):
            add_output('valid')
        if getattr(cfg, 'ctrl_ready'):
            add_input('ready')
        if cfg.hw_read not in ('disabled', 'handshake'):
            add_output('data', field_shape)

        # Generate write interface.
        if cfg.hw_write not in ('disabled', 'stream'):
            add_input('write_data', field_shape)
            if cfg.hw_write != 'status':
                add_input('write_enable')

        # Generate stream-to-mmio interface in canonical signal order.
        if cfg.hw_write == 'stream':
            add_input('valid')
        if cfg.hw_read == 'handshake':
            add_output('ready')
        if cfg.hw_write == 'stream':
            add_input('data', field_shape)

        # Generate per-field control signals.
        for ctrl_signal in ['lock', 'validate', 'invalidate',
                            'clear', 'reset', 'increment', 'decrement']:
            if getattr(cfg, 'ctrl_%s' % ctrl_signal):
                add_input(ctrl_signal)

        # Generate per-bit control signals.
        for bit_signal in ['bit_set', 'bit_clear', 'bit_toggle']:
            if getattr(cfg, 'ctrl_%s' % bit_signal):
                add_input(bit_signal, field_shape)

        # Generate reset value.
        if cfg.reset == 'generic':
            add_generic('reset_data', None, field_shape)
            tple['reset_valid'] = "'1'"
        elif cfg.reset is None:
            if field_shape is None:
                tple['reset_data'] = "'0'"
            else:
                tple['reset_data'] = "(others => '0')"
            tple['reset_valid'] = "'0'"
        else:
            if field_shape is None:
                if cfg.reset:
                    tple['reset_data'] = "'1'"
                else:
                    tple['reset_data'] = "'0'"
            else:
                fmt = ('"{:0%db}"' % field_shape)
                tple['reset_data'] = fmt.format(cfg.reset & ((1 << field_shape) - 1))
            tple['reset_valid'] = "'1'"

        # Generate internal state.
        state_name = 'f_%s_r' % self.field_descriptor.name
        state_record = Record(state_name)
        if field_shape is not None:
            state_record.append('d', std_logic_vector, field_shape)
        else:
            state_record.append('d', std_logic)
        if accum:
            state_record.append(
                'a', std_logic_vector,
                self.field_descriptor.base_bitrange.width + 3)
        state_record.append('v', std_logic)
        if cfg.after_bus_write == 'invalidate':
            state_record.append('inval', std_logic)
        state_array = Array(state_name, state_record)
        state_decl, state_ob = state_array.make_variable(
            state_name, self.field_descriptor.width)
        tple['state'] = state_ob['$i$']
        state_defs = gather_defs(state_array)
        state_defs.append(state_decl + ';')
        self.add_declarations(private='\n'.join(state_defs))

        # Ignore some variables when expanding this template; they will be
        # expanded by the add_field_*_logic() functions.
        tple.passthrough('i', 'r_data', 'w_data', 'w_strobe')

        def expand(block):
            expanded = tple.apply_str_to_str(
                '%s\n\n$%s' % (_TEMPLATE, block), postprocess=False)
            if not expanded.strip():
                expanded = None
            return expanded

        self.add_interface_logic(expand('PRE'), expand('POST'))

        if self.behavior.bus.can_read():
            self.add_read_logic(expand('READ'))

        if self.behavior.bus.can_write():
            self.add_write_logic(expand('WRITE'))
