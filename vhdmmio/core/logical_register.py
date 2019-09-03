"""Submodule for the `LogicalRegister` class."""

from ..config import MetadataConfig
from ..utils import doc_enumerate
from .mixins import Named, Unique, Accessed
from .block import Block

def _enumerate_fields(fields):
    """Enumerates fields using their mnemonics, for use in error messages and
    generated documentation."""
    return doc_enumerate(fields, map_using=lambda field: '`%s`' % field.mnemonic)


def construct_logical_register(resources, regfile, read_fields=None, write_fields=None):
    """Constructs one or two logical registers from sets of read and/or write
    fields. The return value is a two-tuple of the read-mode register and the
    write-mode register. These are `None` if the respective field set was not
    specified or empty. If both sets are specified, the objects returned can
    either be distinct or the same, depending on whether they received
    different metadata."""
    if not read_fields and not write_fields:
        return None, None

    if read_fields is None:
        read_fields = set()
    if write_fields is None:
        write_fields = set()

    # Figure out the metadata for the two access methods.
    def find_reg_meta(fields):
        for field in sorted(fields, key=lambda f: f.bitrange):
            if field.cfg.register_metadata is not None:
                return field.cfg.register_metadata
        return None

    read_meta = find_reg_meta(read_fields)
    write_meta = find_reg_meta(write_fields)

    # If only one of the access methods has metadata associated with it, copy
    # it to the other.
    if read_meta is None:
        read_meta = write_meta
    elif write_meta is None:
        write_meta = read_meta

    # If there is no metadata for this register, generate some based on the
    # fields in it.
    if read_meta is None:
        assert write_meta is None

        field = None
        fields = set()
        if write_fields:
            field = min(write_fields, key=lambda f: f.bitrange)
            fields |= write_fields
        if read_fields:
            field = min(read_fields, key=lambda f: f.bitrange)
            fields |= read_fields
        assert field is not None
        assert fields

        fields = sorted(fields, key=lambda f: f.bitrange)

        read_meta = write_meta = MetadataConfig(
            mnemonic=field.mnemonic,
            name='%s_reg' % field.name,
            brief='register for field%s %s.' % (
                's' if len(fields) != 1 else '',
                _enumerate_fields(fields)))

    # Handle the read-write case with identical metadata.
    if read_meta.name == write_meta.name and read_meta.mnemonic == write_meta.mnemonic:
        if not write_fields:
            read_reg = LogicalRegister(
                resources, regfile, read_meta, 'R/O', read_fields)
            write_reg = None
        elif not read_fields:
            read_reg = None
            write_reg = LogicalRegister(
                resources, regfile, read_meta, 'W/O', write_fields)
        else:
            read_reg = write_reg = LogicalRegister(
                resources, regfile, read_meta, 'R/W', read_fields | write_fields)
    else:
        # Construct the read-only register, if any.
        read_reg = (
            LogicalRegister(
                resources, regfile, read_meta, 'R/O', read_fields)
            if read_fields else None)

        # Construct the write-only register, if any.
        write_reg = (
            LogicalRegister(
                resources, regfile, write_meta, 'W/O', write_fields)
            if write_fields else None)

    # Assign the registers to the fields.
    for field in read_fields | write_fields:
        field.assign_registers(read_reg, write_reg)

    return read_reg, write_reg


class LogicalRegister(Named, Unique, Accessed):
    """Represents a logical register. That is, a collection of one or more
    sequential `Block`s, which in turn represent masked addresses, which (if
    multiple) are to be accessed in sequence to emulate a register wider than
    the bus. A `LogicalRegister` can also be seen as a collection of one or
    more `Field`s that share the same (internal, i.e. including conditions)
    address."""

    def __init__(self, resources, regfile, metadata, mode, fields):
        super().__init__(metadata=metadata, mode=mode)
        with self.context:
            self._regfile = regfile
            self._fields = tuple(sorted(fields, key=lambda f: f.bitrange))

            # Register the names/mnemonics of the register and fields in the
            # register namespace to check for conflicts.
            for field in self.fields:
                resources.register_namespace.add(self, field)

            # Check for behavioral conflicts.
            self._check_behavior()

            # Determine the endianness of the blocks in this logical register.
            self._endianness = self._determine_endianness()

            # Figure out the number of blocks in the logical register.
            bus_width = regfile.cfg.features.bus_width
            msb = max((field.bitrange.high for field in self.fields))
            num_blocks = (msb + bus_width) // bus_width
            assert num_blocks

            # Construct the blocks.
            self._blocks = tuple((
                Block(resources, self, index, num_blocks)
                for index in range(num_blocks)))

    def _check_behavior(self):
        """Helper method for the constructor that checks for behavioral
        conflicts in the fields, for instance a volatile field combined with a
        blocking field."""
        for mode in 'RW':
            if mode not in self._mode:
                continue

            if mode == 'R':
                fields = set(filter(lambda field: field.behavior.bus.can_read(), self.fields))
                volatile = set(filter(lambda field: field.behavior.bus.read.volatile, fields))
                blocking = set(filter(lambda field: field.behavior.bus.read.blocking, fields))
                deferring = set(filter(lambda field: field.behavior.bus.read.deferring, fields))
            else:
                fields = set(filter(lambda field: field.behavior.bus.can_write(), self.fields))
                volatile = set(filter(lambda field: field.behavior.bus.write.volatile, fields))
                blocking = set(filter(lambda field: field.behavior.bus.write.blocking, fields))
                deferring = set(filter(lambda field: field.behavior.bus.write.deferring, fields))

            if volatile and blocking - volatile:
                raise ValueError(
                    'cannot have both volatile fields (%s) and blocking '
                    'fields (%s) in a single register' % (
                        _enumerate_fields(volatile),
                        _enumerate_fields(blocking - volatile)))

            if len(blocking) > 1:
                raise ValueError(
                    'cannot have more than one blocking field in a single '
                    'register (%s)' % (
                        _enumerate_fields(blocking)))

            if deferring:
                if len(fields) > 1:
                    raise ValueError(
                        'deferring fields cannot share a register with other '
                        'fields (%s)' % (
                            _enumerate_fields(deferring)))

    def _determine_endianness(self):
        """Helper method for the constructor that determines the endianness of
        the register based on the register file and field configuration."""
        endianness = None
        for field in self.fields:
            if field.cfg.endianness is not None:
                if endianness is not None:
                    if field.cfg.endianness != endianness:
                        raise ValueError('conflicting endianness specification')
                endianness = field.cfg.endianness
        if endianness is None:
            endianness = self.regfile.cfg.features.endianness
        assert endianness in ('big', 'little')
        return endianness

    @property
    def regfile(self):
        """The register file that this logical register resides in."""
        return self._regfile

    @property
    def fields(self):
        """The fields contained by this logical register as a tuple, in LSB to
        MSB order."""
        return self._fields

    @property
    def address(self):
        """The bus address for this logical register as a `MaskedAddress`. If
        this register has multiple blocks, this corresponds to the address of
        the first block, which is the least significant block in little-endian
        mode, or the most significant in big-endian mode."""
        return self.fields[0].address

    @property
    def internal_address(self):
        """The internal address for this logical register, including
        conditions, as a `MaskedAddress`. If this register has multiple blocks,
        this corresponds to the address of the first block, which is the least
        significant block in little-endian mode, or the most significant in
        big-endian mode."""
        return self.fields[0].internal_address

    def doc_address(self):
        """Formats documentation for this register's internal address. Returns
        a tuple of the formatted address and a list of string representations
        of any additional match conditions."""
        return self.regfile.doc_represent_address(self.internal_address)

    @property
    def endianness(self):
        """Returns the endianness of this register, either `'little'` or
        `'big'`."""
        return self._endianness

    @property
    def little_endian(self):
        """Whether the blocks in this logical register are
        little-endian-ordered. Returns `False` if there is only one block."""
        return len(self._blocks) > 1 and self._endianness == 'little'

    @property
    def big_endian(self):
        """Whether the blocks in this logical register are big-endian-ordered.
        Returns `False` if there is only one block."""
        return len(self._blocks) > 1 and self._endianness == 'big'

    @property
    def blocks(self):
        """The blocks contained by this logical register as a tuple, ordered by
        address. That is, if this register is little-endian, they are ordered
        LSB to MSB; if big-endian, they are ordered MSB to LSB."""
        return self._blocks

    def is_protected(self):
        """Returns whether any of the fields in this logical register are
        prot-sensitive."""
        return any(map(lambda field: field.behavior.bus.is_protected(), self.fields))
