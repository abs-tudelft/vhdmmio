"""Generates the documentation for the register file description."""

import sys
from ..configurable import document_configurables
from .register_file import RegisterFileConfig

if len(sys.argv) != 2:
    print('Dumps vhdmmio\'s generated documentation files.')
    print('usage: %s <output-dir>' % sys.argv[0])
    sys.exit(1)

FRONT_PAGE = """# `vhdmmio`

`vhdmmio` concerns itself with the generation of register files. To
`vhdmmio`, a register file is an AXI4-lite slave, consisting of any number
of fields, occupying the full 4GiB address range provided by AXI4-lite for
as far as the register file is concerned. Normally, not the whole 4GiB
range will be accessible; this is up to the unit that's generating the
addresses. For the "toplevel" register file, this would normally be some
shell or bus infrastructure that only maps a certain address range to it.

`vhdmmio` does not provide any bus infrastructure blocks such as address
decoders/demuxers. Nevertheless, it is possible to connect multiple
register files together in a hierarchical way; one of the field types
`vhdmmio` provides behaves like an AXI4-lite passthrough.

Each register file maps to a single VHDL entity and an accompanying
support package for the component declaration and type definitions needed
for the ports. There is also a common support package (`vhdmmio_pkg.vhd`)
that defines shared data types, most importantly the AXI4-lite records that
`vhdmmio` uses on the entity interfaces (intended to save you a whole lot
of typing when connecting stuff together).

Because of the above, register files in a design are largely independent.
However, AXI4-Lite passthrough fields can refer to other register files in
the design to indicate how the register files are hooked up in the design.
`vhdmmio` can/will be able to use this information to generate more
complete documentation, and to generate C(++) header files/classes and
Python classes for accessing the register file hierarchy as a whole.

The generated register files are human-readable, so if you need to debug or
change something after generation, you should be able to. The entities
consist of a single one-process-style FSM that use variables for state
information, so for debugging you'll need a tool that can trace variables.
Note that this code style implies that all output ports of `vhdmmio`
generated entities are register outputs. This should help a little with
timing closure, but the register files are not intended to be clocked
insanely high. If your active logic requires a high clock speed and
`vhdmmio`'s register files can't keep up, consider a multi-clock design."""

document_configurables(RegisterFileConfig, FRONT_PAGE, sys.argv[1])
