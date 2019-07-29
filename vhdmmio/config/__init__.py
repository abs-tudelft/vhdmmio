"""Submodule containing all the components for the register file configuration
file loader. Calling __main__ on this module generates markdown documentation
for this file."""

from .register_file import RegisterFile
from .register_file_features import RegisterFileFeatures
from .interface_options import InterfaceOptions
from .access_privileges import AccessPrivileges
from .field_descriptor import FieldDescriptor
from .interrupt_descriptor import InterruptDescriptor
from .metadata import Metadata
