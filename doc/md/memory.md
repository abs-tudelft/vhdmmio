# `memory` behavior

This field behavior infers a local memory inside the register file.
The memory can be accessed through the field and/or a single-cycle,
synchronous RAM port generated on the entity interface.

Whether the inferred memory actually maps to memory resources on the
FPGA depends on how smart the synthesizer is. If it doesn't work, use the
`memory-interface` behavior instead, and infer the memory however the
synthesizer expects it to be inferred outside the generated register
file.

This structure supports the following configuration keys.

## `bus-mode`

This key configures the supported bus access modes.

The following values are supported:

 - `read-write` (default): both read and write accesses are supported.

 - `read-only`: only read accesses are supported.

 - `write-only`: only write accesses are supported.

This key is optional unless required by context. If not specified, the default value (`read-write`) is used.

## `hw-mode`

This key configures the supported hardware access modes.

The following values are supported:

 - `read-or-write` (default): a shared read-write interface is generated.

 - `read-and-write`: independent read and write interfaces are generated.

 - `read-only`: only a read interface is generated.

 - `write-only`: only a write interface is generated.

 - `disabled`: no hardware interface is generated.

This key is optional unless required by context. If not specified, the default value (`read-or-write`) is used.

## `portedness`

This key specifies the memory port configuration.

The following values are supported:

 - `auto` (default): `vhdmmio` will choose a fitting configuration based on `bus-mode` and `hw-mode`.

 - `1R`: infer a single-port ROM.

 - `1RW`: infer a RAM with one shared read-write port.

 - `1R1W`: infer a RAM with single independent read and write ports.

 - `2R`: infer a dual-port ROM.

 - `2RW`: infer a RAM with two shared read-write ports.

 - `2R1W`: infer a RAM with two independent read ports and one independent write port.

 - `2R2W`: infer a RAM with two independent read ports and two independent write ports.

This key is optional unless required by context. If not specified, the default value (`auto`) is used.

## `byte-enable`

This key specifies whether this memory should support byte
enables. This is only supported when the bitrange of the field is
byte-aligned.

The following values are supported:

 - `no` (default): no byte write enable signal is created. Any incomplete bus writes result in zeros being written.

 - `yes`: the inferred memory supports a byte write enable signal.

This key is optional unless required by context. If not specified, the default value (`no`) is used.

## `initial-data`

This key specifies the initial data for the inferred memory. Whether
this actually works depends on whether the synthesizer/FPGA
architecture supports inferring initialized memories.

The following values are supported:

 - `null` (default): the memory is not initialized. Simulation yields `'U'`s until the first write.

 - an integer: each memory location is initialized with the given value.

 - a string: the memory is initialized using the given data file. The filename is relative to the configuration file, or relative to the current working directory if the configuration is loaded using the Python API. If the filename ends in `.bin`, the file is treated as little-endian binary; in this case, the width of the memory must be an integer number of bytes. If a different file extension is used, the file is expected to consist of the correct number of spacing-separated integers, such that each integer corresponds to a memory location. These integers can be specified in hexadecimal, binary, or decimal format, selected using the usual `0x`/`0b`/lack of a prefix.

This key is optional unless required by context. If not specified, the default value (`null`) is used.