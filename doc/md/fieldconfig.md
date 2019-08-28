# Field descriptors

A field descriptor describes either a single field or an array of
fields. Each field produced by a field descriptor has exactly the same
characteristics, but maps to a different bitrange, and uses a different
array index on the register file interface. These bitranges are described
by means of a base bitrange (`bitrange`, optionally offset by `address`), a
repeat count (`repeat`) and the necessary strides (`stride`, `field-stride`
and `field-repeat`). Such repetition is useful when you have an array of
similar registers, for instance in a DMA controller with multiple channels,
where each channel has its own set of status and control flags.

Note that this means that you can have four kinds of field descriptors:

 - singular scalar fields,
 - singular vector fields,
 - repeated/array scalar fields, and
 - repeated/array vector fields.

In the VHDL world, scalar vs. vector is distinguished by the base type used
for interface signals: `std_logic` for scalar, and
`std_logic_vector(N-1 downto 0)` for vectors. By default, ports that belong
to the same field are gathered into a record. This record in turn becomes
an array of records for repeated fields, indexed using `(0 to N-1)`. This
record and/or the arrays of `std_logic_vector`s can be flattened away if
needed using the `interface` structure.

The fields themselves as well as the registers they reside in have
identifiers and documentation attachted to them (`mnemonic`, `name`,
`brief`, `doc`, `register-*`). These are obviously used for documentation
generation, but also in the generated code in various ways, depending on
the language backend used. A zero-indexed integer suffix is automatically
added for arrays of fields.

## Behavior

The behavior of the field is determined by the `behavior` key and
associated configuration. There are predefined behaviors for a lot of
functions commonly and less commonly seen in commercial peripheral register
files. On rare occasions where none of the predefined behaviors fit what
you need, you can use the `custom` behavior, which lets you specify the
field-specific VHDL code directly.

Access to the field can optionally be denied based on the AXI4L `aw_prot`
and `ar_prot` fields (`read-deny` and `write-deny`). The VHDL code
generated for the field can be further customized using the `interface`
key.

Field behaviors can be read-write, read-only, or write-only. Read-only
fields can overlap with write-only fields.

## Logical registers and blocks

When parsing a register file description, `vhdmmio` flattens the field
descriptors into fields, and then groups them again by address and
operation (read/write). Such groups are called logical registers.

It is important to note here that even though each field essentially
describes the shape of the logical register that surrounds it using the
addressing keys, logical registers cannot overlap. The only exception
is that a logical register with only write-only fields can overlap/differ
from a logical register with only read-only fields.

A logical register consists of one or more blocks. A block is a single
addressable unit, consisting of a base addess and a mask. The mask allows
the block to be bigger than a single bus word, by ignoring one or more
bits in the comparison. Some field behaviors use these ignored bits for
purposes other than address matching; for example, the AXI passthrough
behavior uses them to construct the downstream bus addresses.

Multiple blocks are assigned to a logical register when it has fields
mapped to it with bit indices beyond the width of the bus; the higher-order
bits carry over into a neighboring block until all fields have a place.
Either little- or big-endian mode can be specified for this; in
little-endian mode the LSB of the logical register resides in the first
block, while in big-endian mode the MSB resides in the first block.

The addresses of the blocks are computed by binary-incrementing the
non-masked bits address. For example, if the base address for a field is
specified to end with binary `10--10--`, consecutive blocks will be at
addresses `10--11--`, `11--00--`, `11--01--`, and so on.

## Atomic access to multi-block registers

`vhdmmio` ensures that logical registers that span multiple blocks are
accessed atomically by means of holding registers. It does so by inferring
central read/write holding registers as large as the largest logical
register in the register file minus the bus width. For reads, reading from
the first block actually performs the read, delivering the low/high word to
the bus immediately (little-/big-endian), and saving the rest in the read
holding register. Reads to the subsequent blocks simply return whatever is
in the holding register. The inverse is done for writes: writing to the
last block actually performs the write, while the preceding accesses write
the data and strobe signals to the write holding register.

The advantage of sharing holding registers is that it reduces the size of
the address decoder and read multiplexer; many addresses taking data from
the same source is advantageous for both area and timing. The primary
disadvantage is that it only works properly when the blocks are accessed
sequentially and completely. It is up to the bus master to enforce this; if
it fails to do so, accesses may end up reading or writing garbage. You can
therefore generally NOT mix purely AXI4L multi-master systems with
multi-block registers.

If you need both multi-block registers and have multiple masters, either
use full AXI4 arbiters and use the `ar_lock`/`aw_lock` signals
appropriately, ensure mutually-exclusive access by means of software
solutions, or implement the desired behavior yourself. The necessary write
holding registers are essentially just `control` fields, while the read
holding registers are `latching` fields.

Multi-block registers with shared holding registers also has security
implications: a malicious piece of code may intentionally try to violate
the aforementioned assumptions to manipulate or eavesdrop accesses made
by another program/bus master. This is particularly important when the
AXI4L `aw_prot` or `ar_prot` signals are used to restrict access to
certain fields. More information on this subject can be found
[here](permissionconfig.md).

## Configuration keys

This structure supports the following configuration keys.

## `behavior`

This key describes the behavior of this field or array of fields.

This key can take the following values:

 - [`primitive`](primitive.md): base class for regular field behavior. Normally not used directly; it's easier to use one of its specializations:

    - Constant fields for reading the design-time configuration of the hardware:

       - [`constant`](constant.md): field which always reads as the same constant value.

       - [`config`](config.md): field which always reads as the same value, configured through a generic.

    - Status fields for monitoring hardware:

       - [`status`](status.md): field which always reflects the current state of an incoming signal.

       - [`internal-status`](internalstatus.md): field which always reflects the current state of an internal signal.

       - [`latching`](latching.md): status field that is only updated by hardware when a write-enable flag is set.

    - Control fields for configuring hardware:

       - [`control`](control.md): basic control field, i.e. written by software and read by hardware.

       - [`internal-control`](internalcontrol.md): like `control`, but drives an internal signal.

    - Flag-like fields for signalling events from hardware to software:

       - [`flag`](flag.md): one flag per bit, set by hardware and explicitly cleared by an MMIO write.

       - [`volatile-flag`](volatileflag.md): like `flag`, but implicitly cleared on read.

       - [`internal-flag`](internalflag.md): like `flag`, but set by an internal signal.

       - [`volatile-internal-flag`](volatileinternalflag.md): combination of `volatile-flag` and `internal-flag`.

    - Flag-like fields for signalling requests from software to hardware:

       - [`strobe`](strobe.md): one flag per bit, strobed by an MMIO write to signal some request to hardware.

       - [`internal-strobe`](internalstrobe.md): one flag per bit, strobed by an MMIO write to signal some request to another `vhdmmio` construct.

       - [`request`](request.md): like `strobe`, but the request flags stay high until acknowledged by hardware.

       - [`multi-request`](multirequest.md): allows multiple software-to-hardware requests to be queued up atomically by counting.

    - Fields for counting events:

       - [`counter`](counter.md): external event counter, reset explicitly by a write.

       - [`volatile-counter`](volatilecounter.md): external event counter, reset implicitly by the read.

       - [`internal-counter`](internalcounter.md): internal event counter, reset explicitly by a write.

       - [`volatile-internal-counter`](volatileinternalcounter.md): internal event counter, reset implicitly by the read.

    - Fields for interfacing with AXI streams:

       - [`stream-to-mmio`](streamtommio.md): field which pops data from an incoming stream.

       - [`mmio-to-stream`](mmiotostream.md): field which pushes data into an outgoing stream.

 - Fields for interfacing with AXI4-lite busses:

    - [`axi`](axi.md): connects a field to an AXI4-lite master port for generating hierarchical bus structures.

 - Fields for interfacing with memories:

    - [`memory`](memory.md): not yet implemented!

 - Fields for controlling `vhdmmio`-managed interrupts:

    - [`interrupt`](interrupt.md): base class for interrupt field behaviors. Normally not used directly; it's easier to use one of its specializations:

    - [`interrupt-flag`](interruptflag.md): interrupt pending flag, cleared by writing ones.

    - [`volatile-interrupt-flag`](volatileinterruptflag.md): interrupt pending flag, cleared by reading.

    - [`interrupt-pend`](interruptpend.md): software-pend field.

    - [`interrupt-enable`](interruptenable.md): interrupt enable control field.

    - [`interrupt-unmask`](interruptunmask.md): interrupt unmask control field.

    - [`interrupt-status`](interruptstatus.md): reflects the masked interrupt flag.

    - [`interrupt-raw`](interruptraw.md): reflects the raw interrupt request.

 - [`custom`](custom.md): allows you to specify the field-specific VHDL code manually.

Depending on the value, additional configuration keys may be supported or required. These must be specified in the same dictionary that this key resides in. Refer to the documentation for the individual values for more information.

## `address`

This key specifies the base address and block mask for the logical
register that the first field described by this descriptor resides
in.

The following values are supported:

 - an integer above or equal to 0: specifies the byte address. The address LSBs that index bytes within the bus word are ignored per the AXI4L specification.

 - a hex/bin integer with don't cares: as before, but specified as a string representation of a hexadecimal or binary integer which may contain don't cares (`-`). The don't care bits mask out address bits in addition to the byte index LSBs. In hexadecimal integers, bit-granular don't-cares can be specified by inserting four-bit binary blocks enclosed in square braces in place of a hex digit.

 - `<address>/<size>`: as before, but the number of ignored LSBs is explicitly set. This is generally a more convenient notation to use when assigning large blocks of memory to a field.

 - `<address>|<ignore>`: specifies the byte address and ignored bits using two integers. Both integers can be specified in hexadecimal, binary, or decimal. A bit which is set in the `<ignore>` value is ignored by the address matcher.

 - `<address>&<mask>`: specifies the byte address and mask using two integers. Both integers can be specified in hexadecimal, binary, or decimal. A bit which is not set in the `<ignore>` value is ignored by the address matcher.

This key is required.

## `conditions`

This key specifies additional address match conditions for the
logical register surrounding the fields described by this descriptor.
These are primarily intended to construct paged or indirect-access
register files, which may be useful when not enough address space is
allocated to the register file to fit all the registers, or when you
want to emulate legacy register files such as a 16550 UART.

The value for this key must match for all fields in the register, so
if you use this, it is recommended to use the `subfields` key to group
all fields that belong to the register together so you only have to
specify it once. In the future, `vhdmmio` may be extended to allow this
value to be field-specific.

This key must be set to a list of dictionaries, of which the structure is defined [here](conditionconfig.md).

This key is optional. Not specifying it is equivalent to specifying an empty list.

## `endianness`

This key specifies the endianness of the logical register
surrounding the fields described by this descriptor.

The following values are supported:

 - `null` (default): the endianness is taken from the global default (little), the register file default specified in the `features` key, or from other fields within the register that do specify a value.

 - `little`: the logical register is little endian. That is, when multiple blocks are needed to describe the field(s), bit 0 of the register resides in the *first* block.

 - `big`: the logical register is big endian. That is, when multiple blocks are needed to describe the field(s), bit 0 of the register resides in the *last* block.

This key is optional unless required by context. If not specified, the default value (`null`) is used.

## `bitrange`

This key specifies the position of the first field described by this
descriptor within the surrounding logical register, and specifies its
vectorness.

Bit indices cannot go below 0, but they can be greater than or equal to
the bus width. In this case, the field "spills over" into the
subsequent block. For instance, for a 32-bit bus and little-endian
endianness, `8:47..8` maps to:

| Address | 31..24 | 23..16 | 15..8  | 7..0   | Block name |
|---------|--------|--------|--------|--------|------------|
| 0x08    | 23..16 | 15..8  |  7..0  |        | `...L`     |
| 0x0C    |        |        | 39..32 | 31..24 | `...H`     |

For big-endian it would be:

| Address | 31..24 | 23..16 | 15..8  | 7..0   | Block name |
|---------|--------|--------|--------|--------|------------|
| 0x08    |        |        | 39..32 | 31..24 | `...H`     |
| 0x0C    | 23..16 | 15..8  |  7..0  |        | `...L`     |

Following the usual nomenclature, 0x08 and 0x0C would be two different
registers, usually called `high` and `low` or some abbreviation
thereof. `vhdmmio` calls 0x08 and 0x0C physical registers (or, more
generally, blocks, which can have an arbitrary bitmask for the
address), which together form a single logical register.

Some output formats require unique names/mnemonics for blocks. Since
names can only be specified for logical registers as a whole, `vhdmmio`
needs to uniquify the identifiers on its own. It does this using the
following rules:

 - logical registers with one block do not receive any name/mnemonic
   suffix.
 - logical registers with two blocks receive `_high`/`H` and `_low`/`L`
   suffixes for their name/mnemonic based on endianness.
 - logical registers with more than two blocks receive alphabetical
   suffixes based on the block index (that is, regardless of
   endianness). The name suffixes have the form `_<lowercase>`, while
   the mnemonic suffixes are simply an uppercase letter.

When the block address bitmask is nontrivial, the "subsequent block"
concept requires further elaboration. Consider for instance the address
`0b10--10--` in a 32-bit register file. You could argue that the next
block is `0b11--10--` or `0b10--11--`. `vhdmmio` opts for the latter.
Specifically, the final block addresses for each block and each of the
the four subaddresses would become:

| Block | Mask          | Sub 0 | Sub 1 | Sub 2 | Sub 3 |
|-------|---------------|-------|-------|-------|-------|
| 0     | ` 0b10--10--` | 0x088 | 0x098 | 0x0A8 | 0x0B8 |
| 1     | ` 0b10--11--` | 0x08C | 0x09C | 0x0AC | 0x0BC |
| 2     | ` 0b11--00--` | 0x0C0 | 0x0D0 | 0x0E0 | 0x0F0 |
| 3     | ` 0b11--01--` | 0x0C4 | 0x0D4 | 0x0E4 | 0x0F4 |
| 4     | ` 0b11--10--` | 0x0C8 | 0x0D8 | 0x0E8 | 0x0F8 |
| 5     | ` 0b11--11--` | 0x0CC | 0x0DC | 0x0EC | 0x0FC |
| 6     | `0b100--00--` | 0x100 | 0x110 | 0x120 | 0x130 |
| ...   | ...           | ...   | ...   | ...   | ...   |

For field descriptors that describe an array of fields through the
`repeat` key, this bitrange specifies the position of the first field
in the array. Subsequent field positions are inferred based on
`field-stride` and `field-repeat`.

The following values are supported:

 - `null` (default): the field occupies the entire bus word, and is thus a vector of the same size as the bus.

 - an integer above or equal to 0: the field occupies a single bit with the specified index, and is thus a scalar.

 - `<high>..<low>`: the field occupies the given inclusive bitrange, and is thus a vector of size `<high>` - `<low>` + 1.

This key is optional unless required by context. If not specified, the default value (`null`) is used.

## `subaddress`

This key specifies how the subaddress for this field is generated.
This subaddress is used for memory-like fields, that need an address in
addition to read/write data.

If you leave this list empty or unspecified, the default is to build
the subaddress by concatenating the masked word address bits. This is
usually what you want. For instance, putting a 64-bit AXI field into a
32-bit register file yields an address like `0b----0--`. The block with
the first halfword then resides at that address, while the block with
the second halfword is at `0b----1--`. The four don't-cares to the left
of the block index bit form the subaddress, which the AXI field uses as
a 64-bit word address, leading to natural ordering.

For more advanced use cases, you can use this key to specify the
structure of the subaddress manually. It must be a list of so-called
components, each of which represents one or more subaddress bits taken
from some source. The source can be the incoming address, an internal
signal, an external input signal, or constant zero. The components are
then concatenated in LSB to MSB order, and optionally summed with
`subaddress_offset` to get the final subaddress.

This key must be set to a list of dictionaries, of which the structure is defined [here](subaddressconfig.md).

This key is optional. Not specifying it is equivalent to specifying an empty list.

## `subaddress-offset`

This key allows you to specify a constant offset for the subaddress.
The value is added to the result of the logic specified by the
`subaddress` key using a full adder before it is passed to the field.
This behavior can not always be emulated by entries in the `subaddress`
key alone due to the ripple carry logic.

Note that subaddresses are usually word-oriented. Fields can be
non-power-of-two-bytes wide, so byte addresses are often
meaningless.

The following values are supported:

 - `0` (default): no offset is applied.

 - a different integer: the given (word) offset is applied to the subaddress.

This key is optional unless required by context. If not specified, the default value (`0`) is used.

## `repeat`

This value specifies whether this field descriptor describes a
single field or an array of fields.

By default, the individual fields are placed in the same register,
as if they were concatenated in LSB to MSB order. This can be
customized using the `field-repeat`, `stride`, and `field-stride`
keys.

The following values are supported:

 - `null` (default): the descriptor describes a single field.

 - an integer above or equal to 1: the descriptor describes an array field of the given size.

This key is optional unless required by context. If not specified, the default value (`null`) is used.

## `field-repeat`

This value specifies how many times this field is repeated within
each logical register before moving on to the next logical register.
For example, a field descriptor with a `repeat` of 7 and a
`field-repeat` of 3 may look like this:

| Address  | Byte 3  | Byte 2  | Byte 1  | Byte 0  |
|----------|---------|---------|---------|---------|
| Base     |         | Field 2 | Field 1 | Field 0 |
| Base + 4 |         | Field 5 | Field 4 | Field 3 |
| Base + 8 |         |         |         | Field 6 |

With `field-repeat` set to `null` instead, they get grouped in the same
logical register, despite becoming wider than the bus (refer to the
docs for `bitrange` for more info):

| Address  | Byte 3  | Byte 2  | Byte 1  | Byte 0  |
|----------|---------|---------|---------|---------|
| Base     | Field 3 | Field 2 | Field 1 | Field 0 |
| (cont.)  |         | Field 6 | Field 5 | Field 4 |

The following values are supported:

 - `null` (default): all fields are placed in the same logical register.

 - `1`: each field gets its own logical register.

 - an integer above or equal to 2: the given amount of fields are placed in each logical register.

This key is optional unless required by context. If not specified, the default value (`null`) is used.

## `stride`

This value specifies by how many blocks the address should be
advanced when moving to the next logical register due to
`field-repeat` < `repeat`.

The following values are supported:

 - `1` (default): the address is incremented by one block. Note that this default is not correct when the logical register is wider than the bus.

 - a different integer: the address is incremented by this amount of blocks each time. Negative numbers can be used for big-endian indexation.

This key is optional unless required by context. If not specified, the default value (`1`) is used.

## `field-stride`

This value specifies by how many bits the bitrange low/high indices
should be advanced when moving to the next field within a single
logical register.

The following values are supported:

 - `null` (default): the bit index is incremented by the width of the field.

 - an integer: the bit index is incremented by this amount of bits each time. Negative values are allowed, as long as the base bitrange is high enough to prevent the final bit indices from falling below zero.

This key is optional unless required by context. If not specified, the default value (`null`) is used.

## Metadata keys

This configuration structure is used to name and document the
field.

More information about this structure may be found [here](metadataconfig.md).

The following configuration keys are used to configure this structure.

### `mnemonic`

This key is documented [here](metadataconfig.md#mnemonic).

### `name`

This key is documented [here](metadataconfig.md#name).

### `brief`

This key is documented [here](metadataconfig.md#brief).

### `doc`

This key is documented [here](metadataconfig.md#doc).

## `register-*`

This optional configuration structure can be used to name and
document the logical register that this field resides in.

Registers can have the same or different metadata attached to them
based on the bus access mode (read/write). In the presence of multiple
metadata sources, the first one encountered in the following list is
used for the read metadata:

 - the register metadata for the least significant readable field in
   the logical register that carries it;
 - the register metadata for the least significant writable field in
   the logical register that carries it;
 - generated from the field metadata for the least significant readable
   field.
 - generated from the field metadata for the least significant writable
   field.

The generated metadata copies the mnemonic from the field, and uses the
field's name with `'_reg'` suffix for the name. The generated brief
just lists the fields in the register.

The priority list is the same for writes, but with points 1 and 2
flipped around (3 and 4 are NOT flipped). If the metadata for the two
access modes resolves to the same object, the register is documented
once as being R/W, even if some fields are read- or write-only and/or
overlap that way. Otherwise, it is documented twice, once as read-only
and once as write-only.

For example, in the 16550 UART, register 0/DLAB 0 is commonly referred
to as the receiver buffer register (`RBR`) in read mode and the
transmitter holding register (`THR`) in write mode, so you might want
to document them separately. On the other hand, you could also document
them once as a FIFO access register (`FAR`, for instance). This is
mostly a matter of taste.

More information about this structure may be found [here](metadataconfig.md).

The following configuration keys are used to configure this structure. This structure is optional, so it is legal to not specify any of them, except when this structure is required by context.

### `register-mnemonic`

This key is documented [here](metadataconfig.md#mnemonic).

### `register-name`

This key is documented [here](metadataconfig.md#name).

### `register-brief`

This key is documented [here](metadataconfig.md#brief).

### `register-doc`

This key is documented [here](metadataconfig.md#doc).

## `read-allow-*`

These keys describe which AXI4L `ar_prot` values are acceptable for
read transactions. By default, the `ar_prot` field is ignored, so all
masters can read from the field(s). These keys have no effect for
write-only fields.

More information about this structure may be found [here](permissionconfig.md).

The following configuration keys are used to configure this structure.

### `read-allow-user`

This key is documented [here](permissionconfig.md#user).

### `read-allow-privileged`

This key is documented [here](permissionconfig.md#privileged).

### `read-allow-secure`

This key is documented [here](permissionconfig.md#secure).

### `read-allow-nonsecure`

This key is documented [here](permissionconfig.md#nonsecure).

### `read-allow-data`

This key is documented [here](permissionconfig.md#data).

### `read-allow-instruction`

This key is documented [here](permissionconfig.md#instruction).

## `write-allow-*`

These keys describe which AXI4L `aw_prot` values are acceptable for
write transactions. By default, the `aw_prot` field is ignored, so all
masters can write to the field(s). These keys have no effect for
read-only fields.

More information about this structure may be found [here](permissionconfig.md).

The following configuration keys are used to configure this structure.

### `write-allow-user`

This key is documented [here](permissionconfig.md#user).

### `write-allow-privileged`

This key is documented [here](permissionconfig.md#privileged).

### `write-allow-secure`

This key is documented [here](permissionconfig.md#secure).

### `write-allow-nonsecure`

This key is documented [here](permissionconfig.md#nonsecure).

### `write-allow-data`

This key is documented [here](permissionconfig.md#data).

### `write-allow-instruction`

This key is documented [here](permissionconfig.md#instruction).

## Interface keys

These keys specify how the VHDL entity interface is generated.

More information about this structure may be found [here](interfaceconfig.md).

The following configuration keys are used to configure this structure.

### `group`

This key is documented [here](interfaceconfig.md#group).

### `flatten`

This key is documented [here](interfaceconfig.md#flatten).

### `generic-group`

This key is documented [here](interfaceconfig.md#generic-group).

### `generic-flatten`

This key is documented [here](interfaceconfig.md#generic-flatten).