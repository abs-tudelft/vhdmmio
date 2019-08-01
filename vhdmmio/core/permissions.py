"""Submodule for handling access privileges based on `prot`."""

from .mixins import Configured

class Permissions(Configured):
    """Represents a parsed set of access permissions."""

    def __init__(self, cfg):
        super().__init__(cfg=cfg)

        # `prot` bit 2.
        if cfg.data and cfg.instruction:
            mask = '-'
        elif cfg.data:
            mask = '0'
        elif cfg.instruction:
            mask = '1'
        else:
            raise ValueError('cannot deny both data and instruction accesses')

        # `prot` bit 1.
        if cfg.secure and cfg.nonsecure:
            mask += '-'
        elif cfg.secure:
            mask += '0'
        elif cfg.nonsecure:
            mask += '1'
        else:
            raise ValueError('cannot deny both secure and nonsecure accesses')

        # `prot` bit 0.
        if cfg.user and cfg.privileged:
            mask += '-'
        elif cfg.user:
            mask += '0'
        elif cfg.privileged:
            mask += '1'
        else:
            raise ValueError('cannot deny both user and privileged accesses')

        self._mask = mask

    @property
    def mask(self):
        """The `prot` bitmask that must match for an access to be allowed
        within the context of these permissions."""
        return self._mask

    @property
    def is_protected(self):
        """Whether any access types are denied."""
        return self._mask != '---'
