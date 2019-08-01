"""Submodule for handling internal signals."""

from .mixins import Shaped, Named, Unique

class Internal(Named, Shaped, Unique):
    """Represents an internal signal."""

    def __init__(self, name, shape):
        super().__init__(shape=shape, name=name)
        self._driver = None
        self._strobers = set()
        self._users = set()

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
        if self._driver is not None:
            raise ValueError(
                'internal %s cannot both be driven by %s and strobed by %s' % (
                    self.name, self._driver, strober))
        self._check_shape(strober, expected_shape)
        self._strobers.add(strober)

    def use(self, user, expected_shape):
        """Registers a user for this internal signal."""
        self._check_shape(user, expected_shape)
        self._users.add(user)

    def verify(self):
        """Raises sensible errors when this internal is missing drivers or
        users, which is probably not what the designer wants."""
        if self._driver is None and not self._strobers:
            raise ValueError(
                'internal %s is not driven by anything' % self._name)
        if not self._users:
            raise ValueError(
                'internal %s is never used' % self._name)


class InternalManager:
    """Storage for internal signals."""

    def __init__(self):
        super().__init__()
        self._internals = {}
        self._io = {}

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
        self._ensure_exists(internal, shape).drive(driver, shape)

    def strobe(self, strober, internal, shape=None):
        """Registers a strober for an internal signal with name `internal` and
        shape `shape`. If `shape` is `None` or left unspecified, the vector
        width can also be specified in `internal` using the `<name>:<width>`
        notation used in various configuration structures."""
        internal, shape = self._parse_internal(internal, shape)
        self._ensure_exists(internal, shape).strobe(strober, shape)

    def use(self, user, internal, shape=None):
        """Registers a user for an internal signal with name `internal` and
        shape `shape`. If `shape` is `None` or left unspecified, the vector
        width can also be specified in `internal` using the `<name>:<width>`
        notation used in various configuration structures."""
        internal, shape = self._parse_internal(internal, shape)
        self._ensure_exists(internal, shape).use(user, shape)

    def make_input(self, internal, shape=None):
        """Registers that the given internal should be driven by an input
        signal of the same name. If `shape` is `None` or left unspecified, the
        vector width can also be specified in `internal` using the
        `<name>:<width>` notation used in various configuration structures."""
        internal, shape = self._parse_internal(internal, shape)
        self.drive('an input port', internal, shape)
        ident = internal.lower()
        if ident in self._io:
            raise ValueError(
                'there is already an I/O port for internal signal %s'
                % internal)
        self._io[ident] = ('in', self._internals[ident])

    def make_output(self, internal, shape=None):
        """Registers that an output signal should be driven by an internal
        signal of the same name. If `shape` is `None` or left unspecified, the
        vector width can also be specified in `internal` using the
        `<name>:<width>` notation used in various configuration structures."""
        internal, shape = self._parse_internal(internal, shape)
        self.drive('an output port', internal, shape)
        ident = internal.lower()
        if ident in self._io:
            raise ValueError(
                'there is already an I/O port for internal signal %s'
                % internal)
        self._io[ident] = ('out', self._internals[ident])

    def __iter__(self):
        """Iterates over all the `Internal` objects."""
        return iter(self._internals.values())

    def inputs(self):
        """Iterates over all the `Internal` signals that are driven by an input
        port with the same name."""
        for _, (direction, internal) in sorted(self._io.items()):
            if direction == 'in':
                yield internal

    def outputs(self):
        """Iterates over all the `Internal` signals that drive an output port
        with the same name."""
        for _, (direction, internal) in sorted(self._io.items()):
            if direction == 'out':
                yield internal

    def verify(self):
        """Verifies the consistency of all stored internals. Raises an
        appropriate `ValueError` if something is wrong."""
        for internal in self:
            internal.verify()
