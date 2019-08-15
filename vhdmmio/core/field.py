"""Submodule for the `Field` class."""

from .mixins import Named, Configured, Unique
from .behavior import Behavior
from .interface_options import InterfaceOptions

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
        with self.context:
            self._descriptor = descriptor
            self._index = index
            self._address = address
            self._internal_address = resources.addressing.construct(
                resources, address, cfg.conditions)
            self._bitrange = bitrange
            self._subaddress = resources.subaddresses.construct(
                resources, self)
            self._behavior = Behavior.construct(
                resources, self,
                cfg.behavior, cfg.read_allow, cfg.write_allow)
            if self._behavior.can_read():
                resources.addressing.read_map(
                    self._internal_address, list).append(self)
            if self._behavior.can_write():
                resources.addressing.write_map(
                    self._internal_address, list).append(self)
            self._interface_options = InterfaceOptions(
                descriptor.regfile.cfg.interface, cfg.interface)

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
    def bitrange(self):
        """The bitrange for this field."""
        return self._bitrange

    @property
    def behavior(self):
        """The behavior object for this field."""
        return self._behavior

    @property
    def subaddress(self):
        """The subaddress construction logic for this field."""
        return self._subaddress

    @property
    def interface_options(self):
        """VHDL interface configuration."""
        return self._interface_options
