"""Submodule for the `RegisterFileConfig` configurable."""

from ..configurable import configurable, Configurable, subconfig, listconfig, protolistconfig
from .metadata import MetadataConfig
from .interface import InterfaceConfig
from .field import FieldConfig
from .interrupt import InterruptConfig
from .features import FeatureConfig

@configurable(name='Register files')
class RegisterFileConfig(Configurable):
    """This is the root configuration structure for `vhdmmio` register
    files."""
    #pylint: disable=E0211,E0213,E0202

    @subconfig
    def metadata():
        """This configuration structure is used to name and document the
        register file."""
        return MetadataConfig

    @subconfig
    def features():
        """This configuration structure is used to specify some options that
        affect register file as a whole."""
        return FeatureConfig

    @subconfig
    def interface():
        """This key specifies the default VHDL entity interface generation
        options for fields and interrupts alike."""
        return InterfaceConfig

    @protolistconfig
    def fields():
        """This key describes the fields that the register file contains."""
        return FieldConfig

    @listconfig
    def interrupts():
        """This key describes the interrupts that the register file
        contains."""
        return InterruptConfig
