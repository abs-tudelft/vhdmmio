from vhdmmio.template import TemplateEngine
import os

class VhdlGenerator:

    def __init__(self, regfiles):
        for regfile in regfiles:
            tple = TemplateEngine()
            tple['r'] = regfile

            # Generate interrupt logic.
            for interrupt in regfile.interrupts:
                comment = interrupt.meta[None].markdown_brief
                assert '\n' not in comment
                if interrupt.can_clear:
                    comment = '@ Edge-sensitive: ' + comment
                else:
                    comment = '@ Level-sensitive: ' + comment
                if interrupt.width is None:
                    tple.append_block('PORTS', comment,
                                      'irq_%s : in std_logic := \'0\';' % interrupt.meta.name)
                    irq_range = '%d' % interrupt.index
                else:
                    tple.append_block('PORTS', comment,
                                      'irq_%s : in std_logic_vector(%d downto 0) '
                                      ':= (others => \'0\');' % (interrupt.meta.name,
                                                                 interrupt.width - 1))
                    irq_range = '%d downto %d' % (interrupt.high, interrupt.low)
                if interrupt.can_clear:
                    tple.append_block('IRQ_LOGIC', comment,
                                      'i_flag({1}) := i_flag({1}) or (irq_{0} and i_enab({1});'
                                      .format(interrupt.meta.name, irq_range))
                else:
                    tple.append_block('IRQ_LOGIC', comment,
                                      'i_flag({1}) := irq_{0} and i_enab({1});'
                                      .format(interrupt.meta.name, irq_range))

            template_file = os.path.dirname(__file__) + os.sep + 'entity.template.vhd'
            print(tple.apply_file_to_str(template_file, comment='-- '))
