
#from .behavior.primitive import Primitive
#print(Primitive.configuration_markdown())

from .field_descriptor import FieldDescriptor
print(FieldDescriptor.configuration_markdown())

for x in FieldDescriptor.markdown_more():
    print(x.configuration_markdown())

#from .behavior.primitive import InternalStatus
#print(InternalStatus.configuration_markdown())
