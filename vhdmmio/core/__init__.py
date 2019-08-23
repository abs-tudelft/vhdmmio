"""Core submodule for `vhdmmio`, containing the class definitions for the
parsed register files."""

from .register_file import RegisterFile
from .field_descriptor import FieldDescriptor
from .field import Field
from .logical_register import LogicalRegister
from .block import Block
# interrupt

from .interface_options import InterfaceOptions
