from vhdmmio.template import TemplateEngine
import os

class VhdlGenerator:

    def __init__(self, regfiles):
        for regfile in regfiles:
            tple = TemplateEngine()
            tple['r'] = regfile

            # Generate interrupt logic.
            if regfile.interrupts:
                ports = ['@ Interrupt inputs.']
                for interrupt in regfile.interrupts:
                    if interrupt.width is None:
                        ports.append('irq_%s : in std_logic;' % interrupt.meta.name)
                    else:
                        ports.append('irq_%s : in std_logic_vector(%s downto 0);' % (
                            interrupt.meta.name, interrupt.width - 1))
                tple.append_block('IRQ_PORTS', ports)

            template_file = os.path.dirname(__file__) + os.sep + 'entity.template.vhd'
            print(tple.apply_file_to_str(template_file, comment='-- '))
