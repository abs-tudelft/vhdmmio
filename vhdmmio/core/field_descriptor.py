"""Submodule for the `FieldDescriptor` class."""

from .mixins import Shaped, Named, Configured, Unique
from .address import MaskedAddress
from .bitrange import BitRange
from .field import Field
from .interface_options import InterfaceOptions
from .behavior import Behavior

class FieldDescriptor(Named, Shaped, Configured, Unique):
    """Represents a parsed field descriptor. That is, a single field or a
    number of fields in an array."""

    def __init__(self, resources, regfile, cfg):
        super().__init__(
            cfg=cfg,
            metadata=cfg.metadata,
            doc_index='' if cfg.repeat is None else '*0..%d*' % (cfg.repeat - 1),
            shape=cfg.repeat)
        with self.context:
            resources.descriptor_namespace.add(self)
            self._regfile = regfile
            self._base_address = MaskedAddress.parse_config(
                self.cfg.address,
                ignore_lsbs=self.regfile.cfg.features.bus_width.bit_length() - 4)
            self._base_bitrange = BitRange.parse_config(
                self.cfg.bitrange,
                width=self.regfile.cfg.features.bus_width,
                flexible=True)
            self._subaddress = resources.construct_subaddress(self)
            self._behavior = Behavior.construct(
                resources, self,
                cfg.behavior, cfg.read_allow, cfg.write_allow)
            self._fields = tuple((
                Field(resources, self, cfg, index, address, bitrange)
                for index, (address, bitrange)
                in enumerate(self._compute_field_locations())))
            self._interface_options = InterfaceOptions(
                regfile.cfg.interface, cfg.interface)

    @property
    def regfile(self):
        """The register file that this field descriptor resides in."""
        return self._regfile

    @property
    def base_address(self):
        """The address for the first field in the descriptor."""
        return self._base_address

    @property
    def base_bitrange(self):
        """The bitrange for the first field in the descriptor."""
        return self._base_bitrange

    @property
    def fields(self):
        """Tuple of fields described by this field descriptor."""
        return self._fields

    @property
    def behavior(self):
        """The behavior object for this fields described by this field
        descriptor."""
        return self._behavior

    @property
    def subaddress(self):
        """The subaddress construction logic for this field descriptor."""
        return self._subaddress

    @property
    def interface_options(self):
        """VHDL interface configuration."""
        return self._interface_options

    def _compute_field_locations(self):
        """Compute and yield the location information for each field described
        by this descriptor as `(address, bitrange)` two-tuples."""

        # Load and substitute defaults for the relative placement configurations.
        field_repeat = self.cfg.field_repeat
        if field_repeat is None:
            field_repeat = self.width
        stride = self.cfg.stride
        field_stride = self.cfg.field_stride
        if field_stride is None:
            field_stride = self.base_bitrange.width

        address = self.base_address
        remain = self.width
        while True:
            for field in range(field_repeat):
                yield address, self.base_bitrange << (field * field_stride)
                remain -= 1
                if not remain:
                    return
            address += stride
