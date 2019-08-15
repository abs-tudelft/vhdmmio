"""Submodule for `Configured` mixin."""

from ...configurable import Configurable

class Configured: #pylint: disable=R0903
    """Mixin for classes which are configured using a `Configurable`."""

    def __init__(self, cfg=None, **kwargs):
        super().__init__(**kwargs)
        if isinstance(cfg, list):
            cfg = tuple(cfg)
        else:
            assert isinstance(cfg, Configurable)
            cfg.freeze()
        self._cfg = cfg

    @property
    def cfg(self):
        """The frozen `Configurable` object used to construct this object."""
        return self._cfg
