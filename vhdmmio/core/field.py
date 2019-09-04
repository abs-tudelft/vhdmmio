"""Submodule for the `Field` class."""

from .mixins import Named, Configured, Unique
from ..utils import doc_enumerate


class FieldSet(set):
    """Represents a set of field, with improved `__str__`."""
    def __init__(self, field):
        super().__init__([field])

    def __str__(self):
        if self:
            return '%s %s' % (
                'field' if len(self) == 1 else 'fields',
                doc_enumerate(self, map_using=lambda f: '"%s"' % f.name))
        return 'empty set of fields'


class Field(Named, Configured, Unique):
    """Represents a parsed field descriptor. That is, a single field or a
    number of fields in an array."""

    def __init__(self, resources, descriptor, cfg, index, address, bitrange):
        index_str = '' if cfg.repeat is None else str(index)
        super().__init__(
            cfg=cfg,
            metadata=cfg.metadata,
            doc_index=index_str,
            mnemonic_suffix=index_str,
            name_suffix=index_str)

        with self.context_if(descriptor.is_vector()):
            if descriptor.is_vector():
                resources.descriptor_namespace.add(self)
            self._descriptor = descriptor
            self._index = index
            self._address = address
            self._internal_address = resources.construct_address(
                address, cfg.conditions)
            self._bitrange = bitrange
            if self.behavior.bus.can_read():
                resources.addresses.read_map(
                    self._internal_address, lambda: FieldSet(self)).add(self)
            if self.behavior.bus.can_write():
                resources.addresses.write_map(
                    self._internal_address, lambda: FieldSet(self)).add(self)

            self._registers_assigned = False
            self._register_read = None
            self._register_write = None

    @property
    def descriptor(self):
        """The field descriptor that this field was described by."""
        return self._descriptor

    @property
    def index(self):
        """The index of this field within the parent field descriptor."""
        return self._index

    @property
    def address(self):
        """The bus address for this field as a `MaskedAddress`."""
        return self._address

    @property
    def internal_address(self):
        """The internal address for this field, including conditions, as a
        `MaskedAddress`."""
        return self._internal_address

    @property
    def register_read(self):
        """The `LogicalRegister` associated with this field in read mode, or
        `None` if this field is write-only."""
        if not self._registers_assigned:
            with self.context:
                raise ValueError('registers have not been assigned yet')
        return self._register_read

    @property
    def register_write(self):
        """The `LogicalRegister` associated with this field in write mode, or
        `None` if this field is write-only."""
        if not self._registers_assigned:
            with self.context:
                raise ValueError('registers have not been assigned yet')
        return self._register_write

    @property
    def bitrange(self):
        """The bitrange for this field."""
        return self._bitrange

    @property
    def behavior(self):
        """The behavior object for this field."""
        return self.descriptor.behavior

    @property
    def subaddress(self):
        """The subaddress construction logic for this field."""
        return self.descriptor.subaddress

    def assign_registers(self, read_reg, write_reg):
        """Assigns registers to this field once they've been constructed. Note
        that this can only be called once, and is supposed to be called during
        register file construction. This object is frozen after register file
        construction completes."""
        if self._registers_assigned:
            with self.context:
                raise ValueError('registers have already been assigned')
        self._register_read = read_reg
        self._register_write = write_reg
        self._registers_assigned = True
