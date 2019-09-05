"""Submodule for `Memory` configurable."""

from ...configurable import configurable, Configurable, choice
#from .registry import behavior, behavior_doc

#behavior_doc('Fields for interfacing with memories:')

#@behavior('memory', 'infers a local memory inside the register file.', 1)
@configurable(name='`memory` behavior')
class Memory(Configurable):
    """This field behavior infers a local memory inside the register file.
    The memory can be accessed through the field and/or a single-cycle,
    synchronous RAM port generated on the entity interface.

    Whether the inferred memory actually maps to memory resources on the
    FPGA depends on how smart the synthesizer is. If it doesn't work, use the
    `memory-interface` behavior instead, and infer the memory however the
    synthesizer expects it to be inferred outside the generated register
    file."""
    #pylint: disable=E0211,E0213

    @choice
    def bus_mode():
        """This key configures the supported bus access modes."""
        yield 'read-write', 'both read and write accesses are supported.'
        yield 'read-only', 'only read accesses are supported.'
        yield 'write-only', 'only write accesses are supported.'

    @choice
    def hw_mode():
        """This key configures the supported hardware access modes."""
        yield 'read-or-write', 'a shared read-write interface is generated.'
        yield 'read-and-write', 'independent read and write interfaces are generated.'
        yield 'read-only', 'only a read interface is generated.'
        yield 'write-only', 'only a write interface is generated.'
        yield 'disabled', 'no hardware interface is generated.'

    @choice
    def portedness():
        """This key specifies the memory port configuration."""
        yield ('auto', '`vhdmmio` will choose a fitting configuration '
               'based on `bus-mode` and `hw-mode`.')
        yield '1R', 'infer a single-port ROM.'
        yield '1RW', 'infer a RAM with one shared read-write port.'
        yield '1R1W', 'infer a RAM with single independent read and write ports.'
        yield '2R', 'infer a dual-port ROM.'
        yield '2RW', 'infer a RAM with two shared read-write ports.'
        yield ('2R1W', 'infer a RAM with two independent read ports and '
               'one independent write port.')
        yield ('2R2W', 'infer a RAM with two independent read ports and '
               'two independent write ports.')

    @choice
    def byte_enable():
        """This key specifies whether this memory should support byte
        enables. This is only supported when the bitrange of the field is
        byte-aligned."""
        yield (False, 'no byte write enable signal is created. Any incomplete '
               'bus writes result in zeros being written.')
        yield (True, 'the inferred memory supports a byte write enable signal.')

    @choice
    def initial_data():
        """This key specifies the initial data for the inferred memory. Whether
        this actually works depends on whether the synthesizer/FPGA
        architecture supports inferring initialized memories."""
        yield (None, 'the memory is not initialized. Simulation yields '
               '`\'U\'`s until the first write.')
        yield int, 'each memory location is initialized with the given value.'
        yield (str, 'the memory is initialized using the given data file. The '
               'filename is relative to the configuration file, or relative to '
               'the current working directory if the configuration is loaded '
               'using the Python API. If the filename ends in `.bin`, the '
               'file is treated as little-endian binary; in this case, the '
               'width of the memory must be an integer number of bytes. If a '
               'different file extension is used, the file is expected to '
               'consist of the correct number of spacing-separated integers, '
               'such that each integer corresponds to a memory location. '
               'These integers can be specified in hexadecimal, binary, or '
               'decimal format, selected using the usual `0x`/`0b`/lack of a '
               'prefix.')
