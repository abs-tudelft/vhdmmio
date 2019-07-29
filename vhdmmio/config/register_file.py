"""Submodule for the `RegisterFile` and `RegisterFileFeatures`
configurables."""

from ..configurable import configurable, Configurable, subconfig, listconfig, protolistconfig
from .metadata import Metadata
from .interface_options import InterfaceOptions
from .field_descriptor import FieldDescriptor
from .interrupt_descriptor import InterruptDescriptor
from .register_file_features import RegisterFileFeatures

@configurable(name='Register files')
class RegisterFile(Configurable):
    """This is the root configuration structure for `vhdmmio` register
    files."""
    #pylint: disable=E0211,E0213,E0202

    @subconfig
    def metadata():
        """This configuration structure is used to name and document the
        register file."""
        return Metadata

    @subconfig
    def features():
        """This configuration structure is used to specify some options that
        affect register file as a whole."""
        return RegisterFileFeatures

    @subconfig
    def interface():
        """This key specifies the default VHDL entity interface generation
        options for fields and interrupts alike."""
        return InterfaceOptions

    @protolistconfig
    def fields():
        """This key describes the fields that the register file contains."""
        return FieldDescriptor

    @listconfig
    def interrupts():
        """This key describes the interrupts that the register file
        contains."""
        return InterruptDescriptor
