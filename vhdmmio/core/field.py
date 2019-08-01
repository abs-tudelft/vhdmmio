"""Submodule for the field descriptor class."""

from .mixins import Named, Configured, Unique
from .bitrange import BitRange
from .permissions import Permissions
from .interface_options import InterfaceOptions

class Field(Named, BitRange, Configured, Unique):
    """Represents a parsed field descriptor. That is, a single field or a
    number of fields in an array."""

    def __init__(self, descriptor, cfg, index, address, bitrange):
        index_str = '' if cfg.repeat is None else str(index)
        super().__init__(
            cfg=cfg,
            metadata=cfg.metadata,
            doc_index=index_str,
            mnemonic_suffix=index_str,
            name_suffix=index_str,
            high_bit=bitrange.high_bit,
            low_bit=bitrange.low_bit if bitrange.is_vector() else None)
        with self.context:
            self._descriptor = descriptor
            self._index = index
            self._address = address
            # TODO: behavior
            # TODO: conditions
            # TODO: subaddress construction
            self._read_allow = Permissions(cfg.read_allow)
            self._write_allow = Permissions(cfg.write_allow)
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
        """The bus address for this field."""
        return self._address

    @property
    def read_allow(self):
        """The read permissions for this field."""
        return self._read_allow

    @property
    def write_allow(self):
        """The write permissions for this field."""
        return self._write_allow

    @property
    def interface_options(self):
        """VHDL interface configuration."""
        return self._interface_options
