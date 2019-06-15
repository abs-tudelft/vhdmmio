"""Module for `Register` object."""

from .metadata import Metadata, ExpandedMetadata
from .accesscaps import ReadWriteCapabilities, AccessCapabilities

class Register(ReadWriteCapabilities):
    """Class representing a register.

    vhdMMIO uses a pretty broad definition for a register. While a register is
    usually just the size of a single bus word, it can be larger in two ways:
    through its block size and its block count. Block size defines how many
    LSBs of the address are ignored when matching the register address; this is
    useful for embedded memories. Block count indicates the number of
    consecutive blocks that are considered to be part of the same logical
    register, to form registers wider than the bus width. Accesses to the wide
    logical register must be done by sequentially accessing each block within
    it: when the last block is written the entire write is processed
    atomically; when the first block is read the remainder of the register is
    stored in a shadow register atomically. Behavior of non-sequential accesses
    is undefined. Multi-word registers always follow little-endian ordering;
    that is, the first block is at the lowest address and maps to the lower
    bits of the logical register."""

    def __init__(self, *fields):
        """Constructs a register from a number of fields. The fields must not
        have had another register assigned to them previously; constructing
        the `Register` object completes all the links, which then become
        immutable."""
        self._read_tag = None
        self._write_tag = None

        # Save the list of fields.
        fields = tuple(sorted(fields, key=lambda f: (
            f.bitrange.low_bit, f.logic.read_caps is None)))
        self._fields = fields
        if not fields:
            raise ValueError('found register with zero fields')

        try:

            # Infer and sanity-check register addressing information.
            self._regfile = fields[0].descriptor.regfile
            self._address = fields[0].bitrange.address
            self._block_size = fields[0].bitrange.size
            for field in fields[1:]:
                assert field.descriptor.regfile == self._regfile
                assert field.bitrange.address == self._address
                if field.bitrange.size != self._block_size:
                    raise ValueError('fields %s and %s are assigned to the same '
                                     'base address, but have different block sizes'
                                     % (fields[0], field))

            # Infer the width and block count of the register.
            bus_width = self._regfile.bus_width
            msb = 0
            for field in fields:
                msb = max(msb, field.bitrange.high_bit)
                assert field.bitrange.bus_width == bus_width
            self._block_count = msb // bus_width + 1
            width = self._block_count * bus_width

            # Infer the bitmap from logical register bit index to field and field
            # index for both read and write operations (independently).
            def populate(write):
                bitmap = [(None, 0)] * width
                caps = []
                for field in fields:
                    field_caps = field.logic.get_caps(write)
                    if field_caps is not None:
                        caps.append(field_caps)
                        for field_idx in range(field.bitrange.width):
                            reg_idx = field_idx + field.bitrange.low_bit
                            if bitmap[reg_idx][0] is not None:
                                raise ValueError('fields %s and %s overlap in %s '
                                                 'mode at bit %d' % (
                                                     field,
                                                     bitmap[reg_idx][0],
                                                     'write' if write else 'read',
                                                     reg_idx))
                            bitmap[reg_idx] = (field, field_idx)
                return tuple(bitmap), AccessCapabilities.check_siblings(caps)
            self._read_bitmap, read_caps = populate(False)
            self._write_bitmap, write_caps = populate(True)

            # Infer metadata for the register.
            for field, _ in self._read_bitmap + self._write_bitmap:
                if field is None:
                    continue
                if field.descriptor.reg_meta is None:
                    continue
                self._meta = field.descriptor.reg_meta[field.index]
                break
            else:
                if len(fields) == 1:
                    meta = fields[0].meta
                    self._meta = Metadata(
                        mnemonic=meta.mnemonic,
                        name=meta.name,
                        brief='',
                        doc='')[None]
                else:
                    raise ValueError('none of the field descriptors mapping to address '
                                     '0x%08X carry metadata for the encompassing '
                                     'register' % self._address)

        except (ValueError, TypeError) as exc:
            field_names = ', '.join((field.meta.name for field in fields[:3]))
            if len(fields) > 3:
                field_names += ', etc.'
            raise type(exc)('while building register with fields %s: %s' % (field_names, exc))
        try:

            # Check for mnemonic conflicts within the fields of this register.
            ExpandedMetadata.check_siblings((field.meta for field in fields))

        except (ValueError, TypeError) as exc:
            raise type(exc)('while building register %s: %s' % (self._meta.name, exc))

        # Connect the fields to this register.
        for field in fields:
            field.register = self

        super().__init__(read_caps=read_caps, write_caps=write_caps)

    @property
    def regfile(self):
        """Points to the register file containing this register."""
        return self._regfile

    @property
    def fields(self):
        """Returns the collection of fields contained by this register."""
        return self._fields

    @property
    def meta(self):
        """Metadata for this group of fields."""
        return self._meta

    @property
    def address(self):
        """Returns the base address for this register."""
        return self._address

    @property
    def block_size(self):
        """Returns this register's block size."""
        return self._block_size

    @property
    def block_count(self):
        """Returns this register's block count."""
        return self._block_count

    @property
    def address_count(self):
        """Returns the number of byte addresses occupied by this register."""
        return self.block_count << self.block_size

    @property
    def address_high(self):
        """Returns the high address for this register."""
        return self.address + self.address_count - 1

    @property
    def bit_count(self):
        """Returns this register's bitcount."""
        return len(self._read_bitmap)

    @property
    def read_bitmap(self):
        """Returns the read bitmap of this register. This is an n-tuple, where
        n is the number of bits in the logical register. Each tuple entry is
        itself a two-tuple of the `Field` the bit maps to, and the bit index
        within the field. If a bit is unmapped, the first entry of the
        two-tuple is `None` instead."""
        return self._read_bitmap

    @property
    def write_bitmap(self):
        """Returns the write bitmap of this register. This is an n-tuple, where
        n is the number of bits in the logical register. Each tuple entry is
        itself a two-tuple of the `Field` the bit maps to, and the bit index
        within the field. If a bit is unmapped, the first entry of the
        two-tuple is `None` instead."""
        return self._write_bitmap

    def get_bitmap(self, write):
        """Returns the bitmap of this register for reading (`!write`) or
        writing (`write`)."""
        return self.write_bitmap if write else self.read_bitmap

    @property
    def read_tag(self):
        """Return the tag used for deferring reads as a VHDL bit vector literal
        including quotes, or `None` if this register cannot defer reads."""
        return self._read_tag

    def assign_read_tag(self, tag):
        """Assigns a read tag to this register."""
        assert self._read_tag is None
        self._read_tag = tag

    @property
    def write_tag(self):
        """Return the tag used for deferring writes as a VHDL bit vector
        literal including quotes, or `None` if this register cannot defer
        writes."""
        return self._write_tag

    def assign_write_tag(self, tag):
        """Assigns a write tag to this register."""
        assert self._write_tag is None
        self._write_tag = tag

    def __str__(self):
        return self.meta.name
