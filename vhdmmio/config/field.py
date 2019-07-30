"""Submodule for `FieldConfig` configurable."""

from ..configurable import (
    configurable, Configurable, choice, parsed, embedded, opt_embedded, select)
from ..core.bitrange import BitRange
from .metadata import MetadataConfig
from .permissions import PermissionConfig
from .interface import InterfaceConfig
from .behavior import behaviors

@configurable(name='Field descriptors')
class FieldConfig(Configurable):
    """A field descriptor describes either a single field or an array of
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

    ## Field behavior

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

    ## Logical registers

    When parsing a register file description, `vhdmmio` flattens the field
    descriptors into fields, and then groups them again by address. Such groups
    are called logical registers.

    `vhdmmio` ensures that logical registers that span multiple blocks/physical
    registers are accessed atomically by means of holding registers. It does so
    by inferring central read/write holding registers as large as the largest
    logical register in the register file minus the bus width. For reads, the
    first access to a multi-block read actually performs the read, delivering
    the low word to the bus immediately, and writing the rest to the holding
    register. Reads to the subsequent addresses simply return whatever is in
    the holding register. The inverse is done for writes: the last access
    actually performs the write, while the preceding accesses write the data
    and strobe signals to the write holding register.

    The advantage of sharing holding registers is that it reduces the size of
    the address decoder, but the primary disadvantage is that it only works
    properly when the physical registers in a logical register are accessed
    sequentially and completely. It is up to the bus master to enforce this; if
    it fails to do so, accesses may end up reading or writing garbage. You can
    therefore generally NOT mix purely AXI4L multi-master systems with
    multi-block registers. If you need both multi-block registers and have
    multiple masters, either use full AXI4 arbiters and use the
    `ar_lock`/`aw_lock` signals appropriately, or ensure mutually-exclusive
    access by means of software solutions.

    Note that this also has security implications: a malicious piece of code
    may intentionally try to violate the aforementioned assumptions to
    manipulate or eavesdrop. This is particularly important when the AXI4L
    `aw_prot` or `ar_prot` signals are used to restrict access to certain
    fields. More information on this subject can be found
    [here](permissionconfig.md)."""

    #pylint: disable=E0211,E0213,E0202

    @select
    def behavior():
        """Describes the behavior of this field or array of fields."""
        for name, cls, brief, level in behaviors():
            yield name, cls, brief, level

    @choice
    def address():
        """This is a byte-oriented address offset for `bitrange`."""
        yield 0, 'no offset.'
        yield int, 'byte-oriented address offset to add to `bitrange`.'

    @parsed
    def bitrange(self, value):
        """The bitrange determines the size of a field and which addresses it
        is sensitive to. It consists of the following components:

         - a byte address;
         - a block size;
         - one or two bit indices.

        The address is what you might expect: it is the AXI4-lite address that
        the associated field responds to. A field can be mapped to more than
        one address however; in this case the byte address is the base address
        (i.e. the lowest address that is part of the bitrange).

        The block size parameter essentially controls how many of the LSBs in
        the AXI4L address are ignored when matching against the base address.
        Normally this is 2 for 32-bit busses and 3 for 64-bit busses, since
        AXI4L addresses are byte-oriented regardless of the bus width and all
        accesses must be aligned. This is also the lower limit.

        When you increase the size parameter beyond the lower limit, the bits
        that are ignored in the address matcher can instead be used by the
        field. Whether the field does anything with this information depends on
        the field type. Examples of fields which use this are memory fields and
        AXI4L passthrough fields.

        The high and low bits (or single bit index) determine the size and
        position of the field in the surrounding logical register. When you
        specify only a single bit index, the field is scalar (think
        `std_logic`); when you specify two, the field is a vector (think
        `std_logic_vector(high downto low)`).

        Bit indices cannot go below 0, but they can be greater than or equal to
        the bus width. In this case, the field "spills over" into the
        subsequent block. For instance, for a 32-bit bus, `8:47..8` maps to:

        | Address | 31..24 | 23..16 | 15..8  | 7..0   |
        |---------|--------|--------|--------|--------|
        | 0x08    | 23..16 | 15..8  |  7..0  |        |
        | 0x0C    |        |        | 39..32 | 31..24 |

        Following the usual nomenclature, 0x08 and 0x0C would be two different
        registers, usually called `high` and `low` or some abbreviation
        thereof. `vhdmmio` calls 0x08 and 0x0C physical registers, which
        together form a single logical register.

        While you would rarely (if ever) do this in practice, `vhdmmio`
        supports combining non-default block sizes with logical registers that
        are wider than the bus. Consider `8/3:47..8` with a 32-bit bus:

        | Address |   31..24   |   23..16   |   15..8    |   7..0     |
        |---------|------------|------------|------------|------------|
        | 0x08    | 23..16 [0] | 15..8 [0]  |  7..0 [0]  |            |
        | 0x0C    | 23..16 [1] | 15..8 [1]  |  7..0 [1]  |            |
        | 0x10    |            |            | 39..32 [0] | 31..24 [0] |
        | 0x14    |            |            | 39..32 [1] | 31..24 [1] |

        For array fields, `address` specifies the bitrange for index 0. The
        bitranges for the remaining indices are generated based on `stride`,
        `field-stride` and `field-repeat`.

        ### Representation

        The bitrange is represented as a string with the following components:

         - `<address>`: byte address represented in decimal, hexadecimal
           (`0x...`), octal (`0...`), or binary (`0b...`). The value set by the
           `address` key is added to this. If no address is specified here, it
           defaults to 0.
         - `/<size>`: the block size represented as an integer.
           Defaults to 2 for 32-bit busses or 3 for 64-bit busses. This syntax
           is kind of like IP subnets, but in reverse; IP subnets specify the
           number of MSBs that *are* matched, whereas bitranges specify the
           number of LSBs that are *not* matched.
         - `:<high>`: the high bit or singular bit that the field
           maps to. If not specified, the field maps to the entire block. That
           is, `high` defaults to the bus width minus one, and `low` defaults
           to 0.
         - `..<low>` (only allowed when `high` is specified): the low bit that
           the field maps to. If not specified, the field maps to a singular
           bit (i.e. it is scalar). Note that `:x..x` differs from `:x`; the
           former generates a vector field of size 1, whereas the latter
           generates a scalar field.

        All these components are optional. Some examples:

         - `0x10:7..0`: 8-bit range residing at the LSB of address 0x10.
         - `0x10`: 32- or 64-bit range at 0x10, depending on bus width.
         - `0x10:5`: single-bit range at bit 5 of address 0x10.
         - `0x10:5..5`: like above, but represents a unit-length array.
         - `0x300/6`: represents an address range from 0x300 to 0x33F.
         - `/10`: represents an address range from 0x000 to 0x3FF.
        """
        address = self.address
        self.address = 0
        return BitRange.from_spec(self.parent.features.bus_width, value).move(address)

    @bitrange.serializer
    def bitrange(value):
        """Serializer for `bitrange`."""
        return BitRange.to_spec(value)

    @choice
    def repeat():
        """This value specifies whether this field descriptor describes a
        single field or an array of fields."""
        yield None, 'the descriptor describes a single field.'
        yield (1, None), 'the descriptor describes an array field of the given size.'

    @choice
    def field_repeat():
        """This value specifies how many times this field is repeated within
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
        """
        yield None, 'all fields are placed in the same logical register.'
        yield 1, 'each field gets its own logical register.'
        yield (2, None), 'the given amount of fields are placed in each logical register.'

    @choice
    def stride():
        """This value specifies by how many bytes the bitrange address should
        be advanced when moving to the next logical register due to
        `field-repeat` < `repeat`."""
        yield None, ('the address is incremented by the field\'s block size. Note that '
                     'this default is not correct when the logical register is wider '
                     'than the bus.')
        yield int, ('the address is incremented by this amount of bytes each time. '
                    'Negative addresses can be used for big-endian indexation.')

    @choice
    def field_stride():
        """This value specifies by how many bits the bitrange low/high indices
        should be advanced when moving to the next field within a single
        logical register."""
        yield None, 'the bit index is incremented by the width of the field.'
        yield int, ('the bit index is incremented by this amount of bits each time. '
                    'Negative values are allowed, as long as the base bitrange is '
                    'high enough to prevent the final bit indices from falling below '
                    'zero.')

    @embedded
    def metadata():
        """This configuration structure is used to name and document the
        field."""
        return MetadataConfig

    @opt_embedded
    def register_metadata():
        """This optional configuration structure is used to name and document
        the logical register that this field resides in. At least one field
        must carry this information for each logical register, unless a single
        field spans the entire register; in this case, the register metadata
        defaults to the field metadata. If more than one field in a logical
        register contains a `register-metadata` tag, the lowest-indexed
        read-mode field takes precedence, unless the register is write-only,
        in which case the lowest-indexed write-mode field takes precedence."""
        return 'register', MetadataConfig

    @embedded
    def read():
        """These keys describe which AXI4L `ar_prot` values are acceptable for
        read transactions. By default, the `ar_prot` field is ignored, so all
        masters can read from the field(s). These keys have no effect for
        write-only fields."""
        return 'read-allow', PermissionConfig

    @embedded
    def write():
        """These keys describe which AXI4L `aw_prot` values are acceptable for
        write transactions. By default, the `aw_prot` field is ignored, so all
        masters can write to the field(s). These keys have no effect for
        read-only fields."""
        return 'write-allow', PermissionConfig

    @embedded
    def interface():
        """These keys specify how the VHDL entity interface is generated."""
        return InterfaceConfig
