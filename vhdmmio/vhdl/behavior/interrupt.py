"""Submodule for interrupt field behavior VHDL code generation."""

from ...template import TemplateEngine, preload_template
from ...core.behavior import InterruptBehavior
from .base import BehaviorCodeGen, behavior_code_gen

_TEMPLATE = preload_template('interrupt.template.vhd', '--')

@behavior_code_gen(InterruptBehavior)
class InterruptBehaviorCodeGen(BehaviorCodeGen):
    """Behavior code generator class for interrupt fields."""

    def generate(self):
        """Code generator implementation."""

        tple = TemplateEngine()
        tple['cfg'] = self.behavior.cfg
        tple['v'] = {
            'raw':    'i_raw{0}',
            'enable': 'i_enab{0}',
            'flag':   'i_flag{0}',
            'unmask': 'i_umsk{0}',
            'masked': '(i_flag{0} and i_umsk{0})',
        }[self.behavior.cfg.mode].format(
            '($i + {0} if isinstance(i, int) else "%s + {0}" % i$)'
            .format(self.behavior.interrupt.offset))

        # Ignore some variables when expanding this template; they will be
        # expanded by the add_field_*_logic() functions.
        tple.passthrough('i', 'r_data', 'w_data', 'w_strobe')

        def expand(block):
            expanded = tple.apply_str_to_str(
                '%s\n\n$%s' % (_TEMPLATE, block), postprocess=False)
            if not expanded.strip():
                expanded = None
            return expanded

        if self.behavior.bus.can_read():
            self.add_read_logic(expand('READ'))

        if self.behavior.bus.can_write():
            self.add_write_logic(expand('WRITE'))
