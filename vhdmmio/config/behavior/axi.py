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
    must be 32 or 64 bits. The number of bus words mapped from the incoming bus
    to the outgoing bus depends on the block size of the field (that is, the
    number of address bits ignored by the field matcher) and the relation
    between the bus widths of the incoming and outgoing busses. It is
    recommended not to do bus width conversion with `vhdmmio` because the
    access pattern is rather unintuitive, but it is fully supported. Using a
    field with `0x100/4` for address and size as an example, the access
    patterns and default address mappings for all combinations of bus widths
    are as follows:

     - 32-bit incoming bus, bitrange `0x100/4` (= `0x100/4:31..0`):

       | Incoming address | Incoming data | Outgoing address | Outgoing data |
       |------------------|---------------|------------------|---------------|
       | 0x000..0x0FC     | n/a           | Unmapped         | n/a           |
       | 0x100            | all           | 0x00             | all           |
       | 0x104            | all           | 0x04             | all           |
       | 0x108            | all           | 0x08             | all           |
       | 0x10C            | all           | 0x0C             | all           |
       | 0x110..*         | n/a           | Unmapped         | n/a           |

     - 64-bit incoming bus, bitrange `0x100/4:31..0`:

       | Incoming address | Incoming data | Outgoing address | Outgoing data |
       |------------------|---------------|------------------|---------------|
       | 0x000..0x0F8     | n/a           | Unmapped         | n/a           |
       | 0x100            | 31..0         | 0x00             | all           |
       | 0x108            | 31..0         | 0x04             | all           |
       | 0x110..*         | n/a           | Unmapped         | n/a           |

     - 32-bit incoming bus, bitrange `0x100/4:63..0`:

       | Incoming address | Incoming data | Outgoing address | Outgoing data |
       |------------------|---------------|------------------|---------------|
       | 0x000..0x0FC     | n/a           | Unmapped         | n/a           |
       | 0x100            | all           | 0x00             | 31..0         |
       | 0x104            | all           | 0x08             | 31..0         |
       | 0x108            | all           | 0x10             | 31..0         |
       | 0x10C            | all           | 0x18             | 31..0         |
       | 0x110            | all           | 0x00             | 63..32        |
       | 0x114            | all           | 0x08             | 63..32        |
       | 0x118            | all           | 0x10             | 63..32        |
       | 0x11C            | all           | 0x18             | 63..32        |
       | 0x120..*         | n/a           | Unmapped         | n/a           |

       Note that to access for instance 0x08 in the outgoing address space,
       0x104 MUST be accessed first, and 0x114 MUST be accessed second,
       following `vhdmmio`'s multi-word register rules.

     - 64-bit incoming bus, bitrange `0x100/4` (= `0x100/4:63..0`):

       | Incoming address | Incoming data | Outgoing address | Outgoing data |
       |------------------|---------------|------------------|---------------|
       | 0x000..0x0F8     | n/a           | Unmapped         | n/a           |
       | 0x100            | all           | 0x00             | all           |
       | 0x108            | all           | 0x08             | all           |
       | 0x110..*         | n/a           | Unmapped         | n/a           |

    `axi` fields support multiple outstanding requests. The amount of
    outstanding requests supported is controlled centrally in the register file
    features structure.
    """
    #pylint: disable=E0211,E0213

    @choice
    def mode():
        """Configures the supported bus access modes."""
        yield 'read-write', 'both read and write accesses are supported.'
        yield 'read-only', 'only read accesses are supported.'
        yield 'write-only', 'only write accesses are supported.'

    @choice
    def interrupt_internal():
        """Configures driving an internal signal high when the
        `vhdmmio`-specific interrupt signal associated with the outgoing AXI4L
        stream is asserted. This internal signal can then be tied to an
        internal interrupt to propagate the flag."""
        yield None, 'the feature is disabled.'
        yield (re.compile(r'[a-zA-Z][a-zA-Z0-9_]*'),
               'an internal signal with the given name is created (if '
               'necessary) and driven by the incoming interrupt signal.')
