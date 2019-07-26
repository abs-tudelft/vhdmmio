"""Submodule for the `RegisterFile` and `RegisterFileFeatures`
configurables."""

from ..config import (
    configurable, Configurable, subconfig, listconfig, protolistconfig, choice, flag)
from .metadata import Metadata
from .interface_options import InterfaceOptions
from .field_descriptor import FieldDescriptor
from .interrupt_descriptor import InterruptDescriptor

@configurable(name='Register file features')
class RegisterFileFeatures(Configurable):
    """This configuration structure specifies some miscellaneous options that
    affect the functionality and generation of the register file as a whole."""
    #pylint: disable=E0211,E0213,E0202

    @choice
    def bus_width():
        """This key specifies the width of the generated AXI4-lite slave
        bus."""
        yield 32, 'the bus uses 32-bit data words.'
        yield 64, 'the bus uses 64-bit data words.'

    @choice
    def max_outstanding():
        """This key specifies the maximum number of outstanding requests per
        operation (read/write) for fields that support this. This value is
        essentially the depth of a FIFO that stores the order in which
        supporting fields were accessed. Since the width of the FIFO is the
        2log of the number of supporting fields, the depth configuration has
        very little effect if there is only one such field (everything but the
        FIFO control logic will be optimized away) and no effect if there is
        no such field."""
        yield 16, 'there can be up to 16 outstanding requests.'
        yield (2, None), 'there can be up to this many outstanding requests.'

    @flag
    def insecure():
        """This key allows you to disable the multi-word register protection
        features normally inferred by `vhdmmio` when any of the fields in the
        register file are sensitive to `aw_prot` or `ar_prot`. This may save
        some area. More information about `vhdmmio`'s security features is
        available [here](accessprivileges.md)."""

    @flag
    def optimize():
        """Normally, `vhdmmio` infers address comparators that match *all* word
        address bits in the incoming request to the field bitranges, such that
        decode errors are properly generated. This can be quite costly in terms
        of area and timing however, since in the worst case each register will
        get its own 30-bit address comparator. Setting this flag to `yes`
        allows `vhdmmio` to assign undefined behavior to unused addresses,
        which lets it minimize the width of these comparators."""


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
