"""Submodule for the root class for a complete register file."""

from .mixins import Named, Configured, Unique
from .resources import Resources
from .field_descriptor import FieldDescriptor

class RegisterFile(Named, Configured, Unique):
    """Compiled representation of a register file."""

    def __init__(self, cfg, trusted):
        self._trusted = trusted
        super().__init__(cfg=cfg, metadata=cfg.metadata)
        with self.context:

            # Create the various resource managers.
            self._resources = Resources()

            # Parse the field descriptors.
            self._field_descriptors = ((
                FieldDescriptor(self._resources, self, fd_cfg)
                for fd_cfg in cfg.fields))

            # The `FieldDescriptor` constructor calls the `Field` constructor,
            # which in turn maps the field addresses to lists of `Field`s in
            # `self._resources.addresses`. We can now convert these lists to
            # `Register`s, of which the constructor also constructs the
            # `Block`s.
            # TODO

    @property
    def trusted(self):
        """Whether source of the configuration used to construct this register
        file is trusted. If not, custom fields are disabled, since their
        template code can execute arbitrary Python code."""
        return self._trusted

    @property
    def field_descriptors(self):
        """Returns the field descriptors of this register file as a tuple."""
        return self._field_descriptors
