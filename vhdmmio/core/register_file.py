"""Submodule for the root class for a complete register file."""

from .mixins import Named
from .internals import InternalManager
from .addressing import AddressManager

class RegisterFile(Named):
    """Compiled representation of a register file."""

    def __init__(self, cfg):
        super().__init__(metadata=cfg.metadata)

        # The configuration is not allowed to mutate after being used to
        # construct a register file.
        cfg.freeze()
        self._cfg = cfg

        # Create the various resource managers.
        self._internals = InternalManager()
        self._addresses = AddressManager()

    @property
    def cfg(self):
        """The frozen `RegisterFileConfig` object used to construct this
        register file."""
        return self._cfg
