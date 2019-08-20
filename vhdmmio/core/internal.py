"""Submodule for handling internal signals."""

from .mixins import Shaped, Named, Unique

class Internal(Named, Shaped, Unique):
    """Represents an internal signal."""

    def __init__(self, name, shape):
        super().__init__(shape=shape, name=name)
        self._driver = None
        self._strobers = set()
        self._users = set()
        self._frozen = False

    def _check_shape(self, obj, expected_shape):
        """Raises a sensible error when `expected_shape` does not match the
        actual shape of this internal."""
        if self.shape != expected_shape:
            raise ValueError(
                '%s expects internal signal %s to be %s, but it is %s' % (
                    obj, self.name, Shaped(expected_shape).describe_shape(),
                    self.describe_shape()))

    def drive(self, driver, expected_shape):
        """Registers a driver for this internal signal."""
        if self._frozen:
            raise ValueError('cannot mutate frozen internal')
        if self._driver is not None:
            raise ValueError(
                'multiple drivers for internal %s: %s and %s' % (
                    self.name, self._driver, driver))
        if self._strobers:
            raise ValueError(
                'internal %s cannot both be driven by %s and strobed by %s' % (
                    self.name, driver, next(iter(self._strobers))))
        self._check_shape(driver, expected_shape)
        self._driver = driver

    def strobe(self, strober, expected_shape):
        """Registers a strober for this internal signal."""
        if self._frozen:
            raise ValueError('cannot mutate frozen internal')
        if self._driver is not None:
            raise ValueError(
                'internal %s cannot both be driven by %s and strobed by %s' % (
                    self.name, self._driver, strober))
        self._check_shape(strober, expected_shape)
        self._strobers.add(strober)

    def use(self, user, expected_shape):
        """Registers a user for this internal signal."""
        if self._frozen:
            raise ValueError('cannot mutate frozen internal')
        self._check_shape(user, expected_shape)
        self._users.add(user)

    def verify_and_freeze(self):
        """Raises sensible errors when this internal is missing drivers or
        users, which is probably not what the designer wants. If successful,
        prevents further modification of the internal."""
        if self._driver is None and not self._strobers:
            raise ValueError(
                'internal %s is not driven by anything' % self._name)
        if not self._users:
            raise ValueError(
                'internal %s is never used' % self._name)
        self._frozen = True

    @property
    def drive_name(self):
        """VHDL variable name to use for driving this signal."""
        if self.is_strobe:
            return 'intsigs_%s' % self.name
        return 'intsig_%s' % self.name

    @property
    def use_name(self):
        """VHDL variable name to use for reading this signal."""
        if self.is_strobe:
            return 'intsigr_%s' % self.name
        return 'intsig_%s' % self.name

    def is_strobe(self):
        """Returns whether this internal is a strobe signal. That is, a signal
        with one or more drivers which only assert it high, while the signal is
        constantly being cleared at the end of each cycle. If `False`, the
        signal is level-driven. Throws an exception when no drivers have been
        assigned yet."""
        if self._driver is None and not self._strobers:
            raise ValueError(
                'internal %s is not driven by anything' % self._name)
        return bool(self._strobers)


class InternalManager:
    """Storage for internal signals."""

    def __init__(self):
        super().__init__()
        self._internals = {}
        self._internal_ios = {}

    def _ensure_exists(self, name, shape):
        """Ensures that an internal signal with `name` and `shape` exists, and
        returns the `Internal` object."""
        ident = name.lower()
        internal = self._internals.get(ident, None)
        if internal is None:
            internal = Internal(name, shape)
            self._internals[ident] = internal
        return internal

    @staticmethod
    def _parse_internal(internal, shape):
        """Parses an internal name that may include shape information using
        `<name>:<width>` syntax. If no width is specified in the name,
        `shape` is used instead."""
        internal, *shape_config = internal.split(':')
        assert not shape_config or shape is None
        if shape_config:
            shape = int(shape_config)
        return internal, shape

    def drive(self, driver, internal, shape=None):
        """Registers a driver for an internal signal with name `internal` and
        shape `shape`. If `shape` is `None` or left unspecified, the vector
        width can also be specified in `internal` using the `<name>:<width>`
        notation used in various configuration structures."""
        internal, shape = self._parse_internal(internal, shape)
        internal_ob = self._ensure_exists(internal, shape)
        internal_ob.drive(driver, shape)
        return internal_ob

    def strobe(self, strober, internal, shape=None):
        """Registers a strober for an internal signal with name `internal` and
        shape `shape`. If `shape` is `None` or left unspecified, the vector
        width can also be specified in `internal` using the `<name>:<width>`
        notation used in various configuration structures."""
        internal, shape = self._parse_internal(internal, shape)
        internal_ob = self._ensure_exists(internal, shape)
        internal_ob.strobe(strober, shape)
        return internal_ob

    def use(self, user, internal, shape=None):
        """Registers a user for an internal signal with name `internal` and
        shape `shape`. If `shape` is `None` or left unspecified, the vector
        width can also be specified in `internal` using the `<name>:<width>`
        notation used in various configuration structures."""
        internal, shape = self._parse_internal(internal, shape)
        internal_ob = self._ensure_exists(internal, shape)
        internal_ob.use(user, shape)
        return internal_ob

    def make_external(self, config):
        """Exposes an external to the outside world based on an
        `InternalIOConfig` structure."""
        if config.direction == 'input':
            internal = self.drive('an input port', config.internal)
        elif config.direction == 'strobe':
            internal = self.strobe('a strobe input port', config.internal)
        else:
            assert config.direction == 'output'
            internal = self.use('an output port', config.internal)

        port = config.port if config.port is not None else internal.name
        ident = port.lower()
        if ident in self._internal_ios:
            raise ValueError(
                'multiple internal I/O ports with name %s' % port)

        self._internal_ios[ident] = (config.direction, internal, port, config.group)

    def __iter__(self):
        """Iterates over all the `Internal` objects."""
        return iter(self._internals.values())

    def iter_internal_ios(self):
        """Iterates over all the ports made using `make_external()`, yielding
        `(direction, internal, port, group)` tuples, similar to the
        configuration structure. However, `internal` is the resolved `Internal`
        signal, and `port` is always defined (if it was `None` in the
        configuration, its default was substituted)."""
        return iter(self._internal_ios.values())

    def verify_and_freeze(self):
        """Verifies the consistency of all stored internals. Raises an
        appropriate `ValueError` if something is wrong."""
        for internal in self:
            internal.verify_and_freeze()
