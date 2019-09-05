"""Submodule for `Block` objects."""

from ..config import MetadataConfig
from .mixins import Named, Unique, Accessed
from .address import AddressSignalMap

class FieldMapping(Unique):
    """Represents a field mapping within a `Block`."""

    def __init__(self, block, field, high, low, offset):
        super().__init__()
        self._block = block
        self._field = field
        self._high = high
        self._low = low
        self._offset = offset
        self._read = field.behavior.bus.can_read() and block.can_read()
        self._write = field.behavior.bus.can_write() and block.can_write()
        assert self._read or self._write
        self._col_span = 1 if high is None else high - low + 1
        self._col_index = block.col_count - offset - self.col_span

    @property
    def field(self):
        """The field that this mapping maps to."""
        return self._field

    @property
    def high(self):
        """The high bit in the field mapped by this mapping, or `None` if the
        field is a single bit."""
        return self._high

    @property
    def low(self):
        """The low bit in the field mapped by this mapping."""
        return self._low

    @property
    def offset(self):
        """The offset of the mapping's low bit in the bus word."""
        return self._offset

    @property
    def read(self):
        """Whether this mapping is used for read accesses."""
        return self._read

    @property
    def write(self):
        """Whether this mapping is used for write accesses."""
        return self._write

    @property
    def col_span(self):
        """The number of table columns occupied by this mapping, assuming that
        columns are used for the bit indices of the bus word. `col_index` is
        then the index of the first column in the table."""
        return self._col_span

    @property
    def col_index(self):
        """The index of the first column in the table, assuming indices start
        at 0 and are MSB-first."""
        return self._col_index

    @property
    def row_span(self):
        """The number of table rows occupied by this mapping, assuming that
        rows are used for the read/write access mode. `row_index` is then the
        index of the first row in the table."""
        return self._block.row_count if self.read and self.write else 1

    @property
    def row_index(self):
        """The index of the first row in the table, assuming read comes first
        if both read and write are specified. If the block is read- or
        write-only, the row is always 0."""
        return 1 if not self.read and self._block.row_count > 1 else 0


class Block(Named, Unique, Accessed):
    """Class representing blocks. A block is a piece of address space
    representable using a single masked address that contains fields,
    accessible in either read mode, write mode, or both. Blocks are equivalent
    to physical registers when only the sub-word LSBs of the address are masked
    out. One or more blocks together form a logical register."""

    def __init__(self, resources, register, index, count):
        # Determine the suffix for the block name.
        if count == 1:
            mnem_suffix = ''
            name_suffix = ''
        elif count == 2:
            if register.endianness == 'little':
                mnem_suffix = 'LH'[index]
            else:
                mnem_suffix = 'HL'[index]
            name_suffix = '_low' if mnem_suffix == 'L' else '_high'
        elif count <= 26:
            mnem_suffix = chr(ord('A') + index)
            name_suffix = '_' + mnem_suffix.lower()
        else:
            raise ValueError('cannot have more than 26 blocks per register')

        # Figure out the bit offset of this block within the logical register.
        bus_width = register.regfile.cfg.features.bus_width
        if register.endianness == 'little':
            offset = index * bus_width
        else:
            offset = (count - index - 1) * bus_width

        # Generate the metadata for this block based on the above.
        metadata = MetadataConfig(
            mnemonic=register.mnemonic + mnem_suffix,
            name=register.name + name_suffix,
            brief='block containing bits %d..%d of register `%s` (`%s`).' % (
                offset + bus_width - 1, offset, register.name, register.mnemonic))

        super().__init__(metadata=metadata, mode=register.mode)
        self._register = register
        self._index = index
        self._offset = offset
        self._internal_address = register.internal_address + index
        self._col_count = bus_width

        # Register ourselves with the address manager while checking for
        # conflicts.
        if self.can_read():
            resources.addresses.read_set(self.internal_address, self)
        if self.can_write():
            resources.addresses.write_set(self.internal_address, self)

        # Figure out our bus address.
        self._address = resources.addresses.signals.split_address(
            self._internal_address)[AddressSignalMap.BUS]

        # If the field that this block belongs to can defer (there is always
        # only one field if this is the case), we need to grab defer tags. In
        # write mode, only the last block needs such a tag; the preceding write
        # buffering can just be done in lookahead mode. For reads, each block
        # needs a tag, since we can only split the read data up into multiple
        # accesses after the deferred access is performed.
        self._read_tag = None
        self._write_tag = None
        for field in register.fields:
            if field.behavior.bus.read is not None and field.behavior.bus.read.deferring:
                assert self._read_tag is None
                self._read_tag = resources.read_tags.get_next()
            if field.behavior.bus.write is not None and field.behavior.bus.write.deferring:
                if index == count - 1:
                    assert self._write_tag is None
                    self._write_tag = resources.write_tags.get_next()

        # If there are multiple blocks, register each block in the register
        # namespace as well. The blocks will get their own definitions and such
        # in the generated software, so they need to be unique.
        if count > 1:
            for field in register.fields:
                resources.register_namespace.add(self, field)

        # Blocks can be described using a table, using the bits of the bus word
        # as the column indices (in natural MSB to LSB order, so reversed) and
        # the access mode as the rows. While the table structure itself is only
        # really relevant for documentation output, we always construct it
        # anyway, because it can be used for conflict detection as well (i.e.
        # intersecting bitranges). Let's first determine the row headers for
        # this block based on its access mode. In the R/W case this is actually
        # temporary; if ALL fields in the block are R/W, the table will be
        # optimized to use a single row later. But construction and usage of
        # the `FieldMapping` objects depends on `self.row_count` working, which
        # depends on `self.row_headers`.
        if self.can_read() and self.can_write():
            self._row_headers = ('R', 'W')
        elif self.can_write():
            self._row_headers = ('W/O',)
        else:
            assert self.can_read()
            self._row_headers = ('R/O',)

        # Construct the double list representing the table cells.
        table = [[None] * self.col_count for _ in range(self.row_count)]

        # Put the fields into the table, reporting conflicts as we go.
        for field in register.fields:

            # Construct the mapping object for this field, or go to the next
            # field if this one does not intersect with this block's range.
            bitrange = field.bitrange
            if bitrange.is_scalar():
                index = bitrange.index - offset
                if index < 0 or index >= bus_width:
                    continue
                mapping = FieldMapping(self, field, None, None, index)
            else:
                low = max(bitrange.low - offset, 0)
                high = min(bitrange.high - offset, bus_width - 1)
                if high < 0 or low >= bus_width:
                    continue
                index = low
                low += offset - bitrange.low
                high += offset - bitrange.low
                mapping = FieldMapping(self, field, high, low, index)

            # Assign the mapping object to the appropriate table cells, while
            # checking for conflicts.
            for row_index in range(mapping.row_index, mapping.row_index + mapping.row_span):
                for col_index in range(mapping.col_index, mapping.col_index + mapping.col_span):
                    old_mapping = table[row_index][col_index]
                    if old_mapping is not None:
                        bit = bus_width - col_index - 1 + offset
                        raise ValueError(
                            'fields `%s` and `%s` intersect at bit %d'
                            % (mapping.field.name, old_mapping.field.name, bit))
                    table[row_index][col_index] = mapping

        # If we have two rows and they are identical, merge them into one.
        if len(table) == 2 and table[0] == table[1]:
            del table[1]
            self._row_headers = ('R/W',)

        # Freeze the cells by turning them into tuples.
        self._table = tuple((tuple(row) for row in table))

        # Also prepare an ordered tuple of all the unique mappings.
        self._mappings = tuple(sorted(
            filter(
                lambda mapping: mapping is not None,
                set((mapping for row in table for mapping in row))),
            key=lambda mapping: (mapping.row_index, mapping.col_index)))

    @property
    def register(self):
        """The register that this block belongs to."""
        return self._register

    @property
    def index(self):
        """The index of this block within the register."""
        return self._index

    @property
    def offset(self):
        """The bit offset to add to the bus word bit indices to get the logical
        register bit indices."""
        return self._offset

    @property
    def address(self):
        """The bus address for this logical register as a `MaskedAddress`. If
        this register has multiple blocks, this corresponds to the address of
        the first block, which is the least significant block in little-endian
        mode, or the most significant in big-endian mode."""
        return self._address

    @property
    def internal_address(self):
        """Internal address of this block (concatenation of the bus address and
        any other match conditions)."""
        return self._internal_address

    @property
    def read_tag(self):
        """The tag used when a field is deferring the bus response to support
        multiple outstanding requests in read mode, or `None` if no such tag is
        needed for this block."""
        return self._read_tag

    @property
    def write_tag(self):
        """The tag used when a field is deferring the bus response to support
        multiple outstanding requests in write mode, or `None` if no such tag
        is needed for this block."""
        return self._write_tag

    def doc_address(self):
        """Formats documentation for this block's internal address. Returns a
        tuple of the formatted address and a list of string representations of
        any additional match conditions."""
        return self.register.regfile.doc_represent_address(self.internal_address)

    @property
    def mappings(self):
        """Tuple of all the `FieldMapping`s, ordered from read to write and
        from MSB to LSB (table order)."""
        return self._mappings

    @property
    def col_count(self):
        """The number of columns in the table representing this bitmap, if
        columns are used for the bit indices and rows for the access modes."""
        return self._col_count

    @property
    def row_count(self):
        """The number of rows in the table representing this bitmap, if columns
        are used for the bit indices and rows for the access modes."""
        return len(self._row_headers)

    @property
    def row_headers(self):
        """The values for the access mode column."""
        return self._row_headers

    @property
    def table(self):
        """Tuples of tuples representing the table cells, row major."""
        return self._table
