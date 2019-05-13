import sys
sys.path.insert(0, '.')
import vhdmmio
from vhdmmio.template import TemplateEngine
import os
engine = TemplateEngine()
engine['NAME'] = 'test_mmio'
engine['DATA_WIDTH'] = 32
engine['N_IRQ'] = 3
engine['IRQ_MASK_RESET'] = '"111"'
engine['IRQ_ENAB_RESET'] = '"1___11"'
filename = os.path.dirname(vhdmmio.__file__) + os.sep + 'vhd' + os.sep + 'entity.template.vhd'
print(engine.apply_file_to_str(filename, '-- '), end='')
