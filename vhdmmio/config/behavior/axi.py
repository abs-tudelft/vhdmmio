"""Submodule for `Axi` configurable."""

import re
from ...configurable import configurable, Configurable, choice
from .registry import behavior, behavior_doc

behavior_doc('Fields for interfacing with AXI4-lite busses:')

@behavior(
    'axi', 'connects a field to an AXI4-lite master port for generating '
    'hierarchical bus structures.', 1)
@configurable(name='`axi` behavior')
class Axi(Configurable):
    """Fields with `axi` behavior map the bus accesses supported by them to a
    different AXI4L bus.

    The width of the outgoing AXI4L bus is set to the width of the field, which
    must therefore be 32 or 64 bits. The *word* address for the outgoing bus is
    taken from the [subaddress](fieldconfig.md#subaddress); the 2 or 3 LSBs of
    the address (depending on the bus width) are always zero. For example, a
    field with address `0x0---` in a 32-bit system has a 10-bit subaddress,
    therefore allowing access to 4kiB of address space on the child AXI4L port.

    Note that going from a 64-bit bus to a 32-bit bus always "stretches" the
    address space of the 32-bit bus, since only half the bus width can be
    utilized. While it would technically be possible to avoid this by just
    doing two transfers on the slave bus for each AXI field access, this adds
    a bunch of complexity, ambiguity, and may prevent read-volatile fields on
    the child bus from being accessed without side effects, so this feature was
    not implemented. Going from a 32-bit bus to a 64-bit bus on the other hand
    is perfectly fine, since this just makes the logical register for the AXI
    field wider than the bus, following `vhdmmio`'s normal rules. Just make
    sure that bit 2 of the field's address is zero.

    `axi` fields support multiple outstanding requests. The amount of
    outstanding requests supported is controlled centrally in the register file
    features structure.
    """
    #pylint: disable=E0211,E0213

    @choice
    def mode():
        """This key configures the supported bus access modes."""
        yield 'read-write', 'both read and write accesses are supported.'
        yield 'read-only', 'only read accesses are supported.'
        yield 'write-only', 'only write accesses are supported.'

    @choice
    def interrupt_internal():
        """This key configures driving an internal signal high when the
        `vhdmmio`-specific interrupt signal associated with the outgoing AXI4L
        stream is asserted. This internal signal can then be tied to an
        internal interrupt to propagate the flag."""
        yield None, 'the feature is disabled.'
        yield (re.compile(r'[a-zA-Z][a-zA-Z0-9_]*'),
               'an internal signal with the given name is created (if '
               'necessary) and driven by the incoming interrupt signal.')

    @choice
    def bus_flatten():
        """This key specifies whether records or flattened signals are desired
        for the bus interface. Note that `flatten` (defined
        [here](interfaceconfig.md#flatten)) should also be set to `yes` to make
        this work."""
        yield (False, 'the bus is not flattened; the records from '
               '`vhdmmio_pkg.vhd` are used.')
        yield (True, 'the bus is flattened; the standard AXI4-lite signal '
               'names are used.')
