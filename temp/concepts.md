Concepts
========


Register files
--------------

`vhdmmio` concerns itself with the generation of register files. To `vhdmmio`,
a register file is an AXI4-lite slave, consisting of any number of fields,
occupying the full 4GiB address range provided by AXI4-lite for as far as the
register file is concerned. Of course, not the whole 4GiB range will normally
be accessible; this is up to the unit that's generating the addresses. For the
"toplevel" register file, this would normally be some shell or bus
infrastructure that only maps a certain address range to it.

`vhdmmio` does not provide any bus infrastructure blocks such as address
decoders/demuxers. Nevertheless, it is possible to connect multiple register
files together in a hierarchical way; one of the field types `vhdmmio` provides
behaves like an AXI4-lite passthrough.

Each register file maps to a single VHDL entity and an accompanying support
package for the component declaration and type definitions needed for the
ports. There is also a common support package (`vhdmmio_pkg.vhd`) that defines
shared data types, most importantly the AXI4-lite records that `vhdmmio` uses
on the entity interfaces (intended to save you a whole lot of typing when
connecting stuff together).

Because of the above, register files in a design are largely independent.
However, AXI4-Lite passthrough fields can refer to other register files in the
design to indicate how the register files are hooked up in the design.
`vhdmmio` can/will be able to use this information to generate more complete
documentation, and to generate C(++) header files/classes and Python classes
for accessing the register file hierarchy as a whole.


Fields
------

Fields are very broadly defined within `vhdmmio`. Specifically, a field is any
piece of (generated) logic that concerns itself with a certain bitrange. A
bitrange is defined by the following parameters:

 - a byte address (`address`);
 - a block size (`size`);
 - one or two bit indices (`high` and `low`).

The address is exactly what you'd expect: this is the AXI4-lite address that
the field is mapped to. A field can be mapped to more than one address however,
using the block size parameter. This is expressed as the number of least
significant address bits that are ignored by the address matcher. This is
particularly useful for AXI passthrough and memory fields, which utilize the
incoming address. The high and low bits (or single bit index) determine which
bits of the bus word the field is mapped to.

Bitranges are usually described as a single string with the following
components:

 - `<address>`: byte address represented in decimal, hexadecimal (`0x...`),
   octal (`0...`), or binary (`0b...`).
 - `/<size>` (optional): the block size represented as an integer. Defaults to
   2 for 32-bit busses or 3 for 64-bit busses. This syntax is kind of like IP
   subnets, but in reverse; IP subnets specify the number of MSBs that *are*
   matched, whereas bitranges specify the number of LSBs that are *not*
   matched.
 - `:<high>` (optional): the high bit or singular bit that the field maps to.
   If not specified, the field maps to the entire block.
 - `..<low>` (optional, only if `high` is specified): the low bit that the
   field maps to. If not specified, the field maps to a singular bit. Note that
   `:x..x` differs from `:x`; the former generates a vector of size 1, whereas
   the latter generates a single bit.

It is also possible for the bit indices to go beyond the width of the bus. When
you do this, the field "spills over" into the subsequent block. For instance,
for a 32-bit bus, `8:47..8` maps to:

| Address | 31..24 | 23..16 | 15..8  | 7..0   |
|---------|--------|--------|--------|--------|
| 0x08    | 23..16 | 15..8  |  7..0  |        |
| 0x0C    |        |        | 39..32 | 31..24 |

This is equivalent to little-endian addressing.

The behavior of a field is determined by its type code. Some examples are
control registers, status registers, constant registers, AXI passthrough,
memories, interrupt control registers, and so on. Most field types have
additional, type-specific parameters that augment the default behavior.

Fields can be read-write, read-only, or write-only. Read-only fields of any
type can overlap with write-only fields of any type.


Field descriptors
-----------------

A field descriptor is a (usually) YAML description of either a single field or
an array of fields. Each field produced by a field descriptor has exactly the
same characteristics, but maps to a different bitrange, and uses a different
array index on the register file interface. These bitranges can be described
either manually as an array or by means of a repeat count and the necessary
strides. Such repetition is useful when you have an array of similar registers,
for instance in a DMA controller with multiple channels, where each channel has
its own set of status and control flags.


Logical registers
-----------------

When parsing a register file description, `vhdmmio` flattens the field
descriptors into fields, and then groups them again by address. Such groups are
called logical registers. We prefix the word "logical", since a logical
register can span multiple bus word addresses due to block size and multi-word
overflow of the bit indices in the fields. We'll call these occupied word
addresses physical registers.

As a silly example, consider a register file with a 32-bit-wide bus with fields
at `0x100/4:47..0` (marked with `/`), `0x100/4:79..48` (marked with `X`), and
`0x100/4:95..80` (marked with `\`):

```
   Incoming                             Address as seen
   address                                 by field
           ,-------------------------------.        -.           -.
    0x100 |//////////// 31..0 //////////////| 0x00    |            |
          |---------------------------------|          > block     |
    0x104 |//////////// 31..0 //////////////| 0x04    |            |
           >===============================<        -'             |
    0x108 |XXXX 15..0 XXXXX|//// 47..32 ////| 0x00                 |  logical
          |----------------+----------------|       -.   physical   > register
    0x10C |XXXX 15..0 XXXXX|//// 47..32 ////| 0x04    :> register  |
           >===============================<        -'             |
    0x110 |\\\\ 15..0 \\\\\|XXXX 31..16 XXXX| 0x00                 |
          |---------------------------------|                      |
    0x114 |\\\\ 15..0 \\\\\|XXXX 31..16 XXXX| 0x04                 |
           `-------------------------------'                     -'

          '-------.,-------'
                 field
```

`vhdmmio` ensures that logical registers that span multiple blocks/physical
registers are accessed atomically by means of holding registers, relying on the
assumption that the complete register is accessed, and that is it accessed
in-sequence. This allows it to perform reads when the first block is accessed
and writes when the last block is accessed, using (shared) holding registers in
between. (Note that this means that the example above is a little silly, since
now you're stuck with a strided access pattern. You would normally make a
register *either* multi-word *or* multi-block, or neither, but not both.)

It is up to the master to ensure that this assumption is valid; if it
is violated, accesses may end up reading or writing garbage. Note that this may
have security implications on multi-threaded systems, since AXI4-lite does not
support locking. `vhdmmio` includes last-resort logic to prevent abuse across
privilege levels if these are used (read holding registers are cleared after a
read completes, interruptions of multi-word accesses by lower-privileged
accesses are blocked) but these should never be relied upon for a secure
system.

Each field can independently respond to a request with an acknowledgement, an
error, or no response at all. These responses are combined to form the
AXI4-lite `resp` field per the following rules:

 - If any field responds with an error, a `slverr` response (`"10"`) is
   generated.
 - Otherwise, if any field responds with an acknowledgement, an `okay` response
   (`"00"`) is generated.
 - If zero fields respond, a `decerr` response (`"11"`) is generated.

Accesses to addresses that do not map to any fields by default return `decerr`
responses as well. However, this leads to wide, 30-bit address matchers. If
needed to meet timing, `vhdmmio` can also optimize the address matcher for you,
treating any accesses to unmapped registers as undefined behavior/don't cares.

Within an access type (read or write), fields can have characteristics that
prevent them from sharing a logical register with other fields. These
characteristics are:

 - Blocking fields: these can block/delay bus access for as long as they
   like. Non-blocking fields always return immediately.

 - Volatile fields: for volatile fields, performing the same operation more
   than once in a row has a different result than performing the operation
   once. Examples of such fields are mmio-to-stream fields, which push data
   into a FIFO for every write, or accumulator fields, which add the written
   value instead of writing it directly.

 - Deferring fields: these can postpone generating a response in a way that
   allows for multiple outstanding requests.

The rules are:

 - Blocking fields cannot be combined with other blocking fields.
 - Blocking fields cannot be combined with volatile fields.
 - Deferring fields cannot be combined with any other field.


Interrupts
----------

In addition to MMIO, `vhdmmio` can handle interrupt routing for you. Each
AXI4-lite bus is equiped with an additional signal in the slave-to-master
direction that serves as an interrupt request flag. This flag is connected to a
(masked) wired-or network of any incoming interrupts you define. The interrupts
can be monitored and controlled through special-purpose fields.

There are up to three internal registers for each interrupt, named `enab`,
`flag`, and `umsk`. `enab` controls whether incoming interrupts are passed on
to the flag register. The flag register stores whether the interrupt is pending
regardless of whether it is enabled; if an interrupt comes in while the
interrupt is enabled, and the interrupt is then disabled, the flag remains
asserted until it is explicitly cleared (usually by an interrupt handler).
`umsk` (unmask) has a similar function, but is placed after the flag register.
Thus, masking an interrupt immediately stops it from being requested, but once
the interrupt is unmasked again, it will be requested again. This logic is
shown schematically below.

```
            .--[raw>
            |         ____                 flag
IRQ --------o--------|    \     _____     .----.   .-[flag>
                     |     )----\    \    |>   |   |         ____
                  .--|____/      )    )---|S  Q|---o--------|    \     to
           enab   |      [pend>-/____/  .-|R   |  umsk      |     )--> wired
          .----.  |      [clear>--------' '----' .----.  .--|____/     OR
          |>   |  |                              |>   |  |
[enable>--|S  Q|--o--[enabled>          [unmask>-|S  Q|--o--[unmasked>
[disable>-|R   |                        [mask>---|R   |
          '----'                                 '----'
```

Each of the three registers are accessible in read, write, set, and clear modes
through special interrupt field types. The raw incoming interrupt signal can
also be monitored directly.

Interrupts can be made level-sensitive by not specifying a way to clear the
interrupt. In this case, the logic is automatically simplified to the
following.

```
            .--[raw>
            |         ____                 .-[flag>
IRQ --------o--------|    \                |         ____
                     |     )---------------o--------|    \     to
                  .--|____/                         |     )--> wired
           enab   |                       umsk   .--|____/     OR
          .----.  |                      .----.  |
          |>   |  |                      |>   |  |
[enable>--|S  Q|--o--[enabled>  [unmask>-|S  Q|--o--[unmasked>
[disable>-|R   |                [mask>---|R   |
          '----'                         '----'
```

Furthermore, if there is no way to enable/unmask an interrupt, the respective
AND gate and the register is effectively optimized away. If there *is* a way,
the reset state is disabled/masked.


Metadata
--------

Register files, logical registers, fields, and interrupts all carry the same
kind of metadata object to identify and describe them. Such a metadata object
consists of up to four parameters:

 - `mnemonic` (optional): an uppercase-only identifier, usually just two or
   three letters. These are commonly used to concisely refer to fields within
   a register. Therefore, for fields, they only need to be unique within the
   surrounding logical register.

 - `name`: a regular identifier that uniquely identifies a register file within
   a design, or a field/register/interrupt within a register file.

 - `brief` (optional): a one-line/single-sentence markdown-formatted string
   that briefly describes the object.

 - `doc` (optional): a multiline markdown-formatted string describing the
   object more thoroughly.

`mnemonic` and `brief` are derived from `name` when they are not specified.
