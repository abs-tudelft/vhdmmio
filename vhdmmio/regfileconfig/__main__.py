
#from .behavior.primitive import Primitive
#print(Primitive.configuration_markdown())

#from .field_descriptor import FieldDescriptor
#print(FieldDescriptor.configuration_markdown())

#for x in FieldDescriptor.markdown_more():
    #print(x.configuration_markdown())

#from .behavior.primitive import InternalStatus
#print(InternalStatus.configuration_markdown())

from plumbum import local
from ..config import document_configurables
from .field_descriptor import FieldDescriptor

local['rm']('-rf', 'mdbook/src')
local['mkdir']('-p', 'mdbook/src')
document_configurables(FieldDescriptor, 'mdbook/src')
with local.cwd('mdbook'):
    local['mdbook']('build')
