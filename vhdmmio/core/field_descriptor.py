"""Submodule for the field descriptor class."""

from .mixins import Shaped, Named, Configured, Unique
from .addressing import MaskedAddress
from .bitrange import BitRange
from .field import Field

class FieldDescriptor(Named, Shaped, Configured, Unique):
    """Represents a parsed field descriptor. That is, a single field or a
    number of fields in an array."""

    def __init__(self, regfile, cfg):
        super().__init__(
            cfg=cfg,
            metadata=cfg.metadata,
            doc_index='' if cfg.repeat is None else '*0..%d*' % (cfg.repeat - 1),
            shape=cfg.repeat)
        with self.context:
            self._regfile = regfile
            self._fields = tuple((
                Field(self, cfg, index, address, bitrange)
                for index, (address, bitrange)
                in enumerate(self._compute_field_locations())))

    @property
    def regfile(self):
        """The register file that this field descriptor resides in."""
        return self._regfile

    @property
    def fields(self):
        """Tuple of fields described by this field descriptor."""
        return self._fields

    def _compute_field_locations(self):
        """Compute and yield the location information for each field described
        by this descriptor as `(address, bitrange)` two-tuples."""

        # Parse the address and bitrange.
        bus_width = self.regfile.cfg.features.bus_width
        address = MaskedAddress.parse_config(
            self.cfg.address, ignore_lsbs=bus_width.bit_length() - 4)
        bitrange = BitRange.parse_config(self.cfg.bitrange, bus_width=bus_width)

        # Load and substitute defaults for the relative placement configurations.
        field_repeat = self.cfg.field_repeat
        if field_repeat is None:
            field_repeat = self.width
        stride = self.cfg.stride
        field_stride = self.cfg.field_stride
        if field_stride is None:
            field_stride = bitrange.width

        remain = self.width
        while True:
            for field in range(field_repeat):
                yield address, bitrange << (field * field_stride)
                remain -= 1
                if not remain:
                    return
            address += stride
