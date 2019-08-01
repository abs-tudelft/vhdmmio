"""Submodule for handling access privileges based on `prot`."""

class InterfaceOptions:
    """Represents a parsed set of interface options, built from one or more
    `InterfaceConfig` objects."""

    def __init__(self, *cfgs):
        super().__init__()

        # Set global defaults.
        self._port_group = False
        self._port_flatten = 'never'
        self._generic_group = False
        self._generic_flatten = 'all'

        # Override defaults with the values from cfgs.
        for cfg in cfgs:
            if cfg.group is not None:
                self._port_group = cfg.group
            if cfg.flatten is False:
                self._port_flatten = 'never'
            elif cfg.flatten == 'record':
                self._port_flatten = 'record'
            elif cfg.flatten is True:
                self._port_flatten = 'all'
            if cfg.generic_group is not None:
                self._generic_group = cfg.generic_group
            if cfg.generic_flatten is False:
                self._generic_flatten = 'never'
            elif cfg.generic_flatten == 'record':
                self._generic_flatten = 'record'
            elif cfg.generic_flatten is True:
                self._generic_flatten = 'all'

        # None is used for "use default" for groups above, but for
        # "do not group" below.
        if not self._port_group:
            self._port_group = None
        if not self._generic_group:
            self._generic_group = None

    @property
    def port_group(self):
        """The port group to use for this object as a string, or `None` if no
        group is to be used."""
        return self._port_group

    @property
    def port_flatten(self):
        """The port flattening mode to use for this object. Either `'never'`,
        `'record'` or `'all'` to indicate the desired mode."""
        return self._port_flatten

    @property
    def generic_group(self):
        """The generic group to use for this object as a string, or `None` if
        no group is to be used."""
        return self._generic_group

    @property
    def generic_flatten(self):
        """The generic flattening mode to use for this object. Either
        `'never'`, `'record'` or `'all'` to indicate the desired mode."""
        return self._generic_flatten
