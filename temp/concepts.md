Concepts
========


Register files
--------------

`vhdmmio` concerns itself with the generation of register files. To `vhdmmio`,
a register file is an AXI4-lite slave, consisting of any number of fields,
occupying the full 4GiB address range provided by AXI4-lite for as far as the
register file is concerned. Normally, not the whole 4GiB range will be
accessible; this is up to the unit that's generating the addresses. For the
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

The generated register files are human-readable, so if you need to debug or
change something after generation, you should be able to. The entities consist
of a single one-process-style FSM that use variables for state information, so
for debugging you'll need a tool that can trace variables. Note that this
code style implies that all output ports of `vhdmmio`-generated entities are
register outputs. This should help a little with timing closure, but the
register files are not intended to be clocked insanely high. If your active
logic requires a high clock speed and `vhdmmio`'s register files can't keep
up, consider a multi-clock design.


Metadata
--------

`vhdmmio` can also generate documentation for its register files. In order for
this documentation to actually be useful as such, it requires more information
for each generated construct than just an identifier. The information that you
can provide is standardized into four parameters, with increasing verbosity:

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


Fields and bitranges
--------------------

Fields are very broadly defined within `vhdmmio`. Specifically, a field is any
piece of (generated) logic that concerns itself with a certain bitrange. A
bitrange is also quite broadly defined; it consists of the following
parameters:

 - a byte address (`address`);
 - a block size (`size`);
 - one or two bit indices (`high` and `low`).

The address is what you might expect: it is the AXI4-lite address that the
associated field responds to. A field can be mapped to more than one address
however; in this case the byte address is the base address (i.e. the lowest
address that is part of the bitrange).

The block size parameter essentially controls how many of the LSBs in the
AXI4L address are ignored when matching against the base address. Normally
this is 2 for 32-bit busses and 3 for 64-bit busses, since AXI4L addresses are
byte-oriented regardless of the bus width and all accesses must be aligned.
This is also the lower limit.

When you increase the size parameter beyond the lower limit, the bits that are
ignored in the address matcher can instead be used by the field. Whether the
field does anything with this information depends on the field type. Examples
of fields which use this are memory fields and AXI4L passthrough fields.

The high and low bits (or single bit index) determine the size and position of
the field in the surrounding so-called logical register. When you specify only
a single bit index, the field is scalar (think `std_logic`); when you specify
two, the field is a vector (think `std_logic_vector(high downto low)`).

Bit indices cannot go below 0, but they can be greater than or equal to the bus
width. In this case, the field "spills over" into the subsequent block. For
instance, for a 32-bit bus, `8:47..8` maps to:

| Address | 31..24 | 23..16 | 15..8  | 7..0   |
|---------|--------|--------|--------|--------|
| 0x08    | 23..16 | 15..8  |  7..0  |        |
| 0x0C    |        |        | 39..32 | 31..24 |

Following the usual nomenclature, 0x08 and 0x0C would be two different
registers, usually called `high` and `low` or some abbreviation thereof.
`vhdmmio` calls 0x08 and 0x0C physical registers, which together form a single
logical register.

While you would rarely do this in practice, `vhdmmio` supports combining
non-default block sizes with logical registers that are wider than the bus.
Consider `8/3:47..8` with a 32-bit bus:

| Address |   31..24   |   23..16   |   15..8    |   7..0     |
|---------|------------|------------|------------|------------|
| 0x08    | 23..16 [0] | 15..8 [0]  |  7..0 [0]  |            |
| 0x0C    | 23..16 [1] | 15..8 [1]  |  7..0 [1]  |            |
| 0x10    |            |            | 39..32 [0] | 31..24 [0] |
| 0x14    |            |            | 39..32 [1] | 31..24 [1] |

We need some more definitions now. Following regular nomenclature, the
individual addresses still map to one physical register each. `0x08+0x0C`
and `0x10+0x14` are each called a block (hence the earlier term block size).
The entire range from 0x08 to 0x14 (or 0x17, depending on how you look at it)
forms the logical register.

Notice that logical registers need not be aligned by their size – they can in
fact consist of a non-power-of-two amount of blocks. This is why bits that go
beyond the bus word are mapped to the next block instead of the next physical
register; a div/mod unit would be needed in the worst case if it weren't for
this.

Bitranges are usually represented as a single string with the following
components:

 - `<address>`: byte address represented in decimal, hexadecimal (`0x...`),
   octal (`0...`), or binary (`0b...`).
 - `/<size>` (optional): the block size represented as an integer. Defaults to
   2 for 32-bit busses or 3 for 64-bit busses. This syntax is kind of like IP
   subnets, but in reverse; IP subnets specify the number of MSBs that *are*
   matched, whereas bitranges specify the number of LSBs that are *not*
   matched.
 - `:<high>` (optional): the high bit or singular bit that the field maps to.
   If not specified, the field maps to the entire block. That is, `high`
   defaults to the bus width minus one, and `low` defaults to 0.
 - `..<low>` (optional, only if `high` is specified): the low bit that the
   field maps to. If not specified, the field maps to a singular bit (i.e. it
   is scalar). Note that `:x..x` differs from `:x`; the former generates a
   vector field of size 1, whereas the latter generates a scalar field.

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
by means of a repeat count and the necessary strides. Such repetition is useful
when you have an array of similar registers, for instance in a DMA controller
with multiple channels, where each channel has its own set of status and
control flags.

Note that this means that you can have four kinds of field descriptors:

 - singular scalar fields, represented as `std_logic` where applicable;
 - singular vector fields, represented as `std_logic_vector` where applicable;
 - repeated/array scalar fields, represented as `std_logic_array` where
   applicable;
 - repeated/array vector fields, represented as an custom array of
   appropriately sized `std_logic_vector`s.

Note that `vhdmmio` distinguishes between vectors and arrays in the types as
well (`std_logic_array`). The difference is that vectors always have a `downto`
range, and arrays always have a `to` range.


Logical registers
-----------------

When parsing a register file description, `vhdmmio` flattens the field
descriptors into fields, and then groups them again by address. As we've seen
before, such groups are called logical registers.

`vhdmmio` ensures that logical registers that span multiple blocks/physical
registers are accessed atomically by means of holding registers. It does so by
inferring central read/write holding registers as large as the largest logical
register in the register file minus the bus width. For reads, the first access
to a multi-block read actually performs the read, delivering the low word to
the bus immediately, and writing the rest to the holding register. Reads to the
subsequent addresses simply return whatever is in the holding register. The
inverse is done for writes: the last access actually performs the write, while
the preceding accesses write the data and strobe signals to the write holding
register.

The advantage of sharing holding registers is that it reduces the size of the
address decoder, but the primary disadvantage is that it only works properly
when the physical registers in a logical register are accessed sequentially
and completely. It is up to the bus master to enforce this; if it fails to do
so, accesses may end up reading or writing garbage. You can therefore
generally NOT mix purely AXI4L multi-master systems with multi-block registers.
If you need both multi-block registers and have multiple masters, either use
full AXI4 arbiters and use the `ar_lock`/`aw_lock` signals appropriately, or
ensure mutually-exclusive access by means of software solutions.

Note that this also has security implications: a malicious piece of code may
intentionally try to violate the aforementioned assumptions to manipulate or
eavesdrop. This is particularly important when the AXI4L `prot` field is used
to restrict access to certain fields based on privilege levels. `vhdmmio` by
default includes a small amount of last-resort logic that rejects
lesser-privileged transfers entirely when a higher-privilege multi-block access
is ongoing and clears the read holding registers when a read completes. This
is still susceptable to side-channel attacks (among other things, probably).
Do NOT rely solely on this feature to secure a system. If you know for sure
that you don't need this logic but still want to use the `prot` field, you
can disable it on a per-register-file basis.


Field logic
-----------

When a logical register is accessed, each field can independently respond to
the request by acknowledging it, rejecting it, ignoring it, blocking it, or
deferring it. The logic that handles the request and generates this response
is called the field logic. The responses of the individual fields are combined
into a single action as follows:

 - If any field defers the request, the request is handshaked, but no response
   is sent yet. Instead, the field logic is addressed again later to get the
   response, at which point it must perform any of the following actions.
 - If any field blocks the request, the request stays in its holding register.
   Thus, the same request will appear again in the next cycle.
 - Otherwise, if any field rejects the request, the request is handshaked and
   a `slverr` response (`"10"`) is sent.
 - Otherwise, if any field responds with an acknowledgement, the request is
   handshaked an `okay` response (`"00"`) is sent.
 - If zero fields respond, the request is handshaked and a `decerr` response
   (`"11"`) is sent.

Deferral allows fields such as AXI passthrough fields to handle multiple
outstanding requests. Such deferral logic (particularly the required FIFO) is
only generated for register files and logical registers that need it.

Accesses to addresses that do not map to any fields by default return `decerr`
responses, since there is no field logic to generate a response. `vhdmmio` can
however be instructed to "optimize" its address decoder by treating accesses
that do not map to any field as don't care. This usually prevents wide
equal-to-constant blocks from being inferred, potentially improving timing
performance.

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

Fields must also specify how (or if) a master can choose to not access a
field (or rather, prevent side effects) while still accessing other fields in
the surrounding logical register. The options are:

 - *always*: all accesses are no-op for the field. This is usually the case for
   reads, but not always.
 - *write zero*: writing zeros to the field is no-op. This is usually the case
   for flag and counter fields.
 - *write current*: first read the register, then write the bits that were read
   to it for no-op.
 - *mask*: bits masked out by the AXI4L byte strobe field are not affected.
 - *write current or mask*: both of the above methods will work. This is
   usually the case for control registers.
 - *never*: it is impossible to access this register without causing side
   effects for this field. This is for instance the case for AXI4L passthrough
   fields.


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


Internal signals
----------------

Some of the more advanced features of `vhdmmio` require custom routing between
interrupts and fields. For instance, `vhdmmio` can generate MMIO to stream
fields that have a custom, internal action associated with them for when the
master is writing to the field while the stream is not ready. A common example
of this is asserting an overflow interrupt. To this end, `vhdmmio` supports
generation of internal signals.

Internal signals consist of a name used to refer to it, a driver or a list of
strobers, and a list of users. For an internal signal to be considered valid,
the following things must be true:

 - all constructs that refer to it agree on whether it's a scalar or vector,
   and on the vector width if the latter;
 - there is one driver *or* there are one or more strobers;
 - there is at least one user.

Drivers and strobers both assign to the signal. The difference is that the
driver of a driven signal has full control over the underlying variable, while
strobers are only allowed to set it (wired-or). Whether a construct drives or
strobes an internal signal depends on the nature of the construct.
