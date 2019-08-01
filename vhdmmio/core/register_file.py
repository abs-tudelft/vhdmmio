"""Submodule for the root class for a complete register file."""

from .mixins import Named, Configured, Unique
from .internals import InternalManager
from .addressing import AddressManager
from .field_descriptor import FieldDescriptor

class RegisterFile(Named, Configured, Unique):
    """Compiled representation of a register file."""

    def __init__(self, cfg):
        super().__init__(cfg=cfg, metadata=cfg.metadata)
        with self.context:

            # Create the various resource managers.
            self._internals = InternalManager()
            self._addresses = AddressManager()

            # Parse the field descriptors.
            self._field_descriptors = ((
                FieldDescriptor(self, fd_cfg)
                for fd_cfg in cfg.fields))

    @property
    def field_descriptors(self):
        """Returns the field descriptors of this register file as a tuple."""
        return self._field_descriptors
