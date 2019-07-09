"""Registry for custom internal control signals. Internal signals are usually
driven by fields, to be used for paging or producing interrupts."""

import re

class InternalSignalRegistry:
    """Registry for internal signals within a register file."""

    def __init__(self):
        super().__init__()
        self._signals = {}

    def _get_signal(self, user, name, width):
        """Helper function that ensures existence of an internal signal with
        the specified name and width and returns it."""
        signal = self._signals.get(name)
        if signal is None:
            signal = InternalSignal(name, width)
            self._signals[name] = signal
        else:
            signal.check_width(user, width)
        return signal

    def drive(self, driver, name, width=None):
        """Registers an internal signal driver. `driver` can be any object with
        an appropriate `__str__()` for error messages. `name` is a unique
        signal name (must be an identifier). `width` must be `None` to drive an
        `std_logic` or an integer bitcount to drive an `std_logic_vector`."""
        signal = self._get_signal(driver, name, width)
        signal.driver = driver
        return signal

    def strobe(self, strober, name, width=None):
        """Registers an internal signal strobe driver. Strobe drivers can only
        bit-set the signal, while the signal is centrally cleared at the start
        of each cycle. To ensure consistency regardless of where drivers and
        users are defined in the process with respect to each other, reads are
        delayed by one cycle. `driver` can be any object with an appropriate
        `__str__()` for error messages. `name` is a unique signal name (must be
        an identifier). `width` must be `None` to drive an `std_logic` or an
        integer bitcount to drive an `std_logic_vector`."""
        signal = self._get_signal(strober, name, width)
        signal.add_strober(strober)
        return signal

    def use(self, user, name, width=None):
        """Registers an internal signal user. `user` can be any object with an
        appropriate `__str__()` for error messages. `name` is a unique signal
        name (must be an identifier). `width` must be `None` when an
        `std_logic` is expected, or an integer bitcount when an
        `std_logic_vector` is expected."""
        signal = self._get_signal(user, name, width)
        signal.add_user(user)
        return signal

    def check_consistency(self):
        """Checks consistency for all signals. Signals must have exactly one
        driver and one or more users to be consistent. Raises an appropriate
        error if the check fails, otherwise returns `None`."""
        for signal in self:
            signal.check_consistency()

    def __iter__(self):
        """Yields all registered `InternalSignal`s."""
        return iter(self._signals.values())


class InternalSignal:
    """Represents an internal signal within a register file."""

    def __init__(self, name, width=None):
        """Constructs an internal signal with the given name and vector width.
        If `width` is `None`, an `std_logic` is produced instead of an
        `std_logic_vector`."""
        super().__init__()
        self._name = name
        self._width = width
        self._driver = None
        self._strobers = []
        self._users = []

        if not re.match(r'[a-zA-Z][a-zA-Z_0-9]*$', self._name):
            raise ValueError('name {!r} is not a valid identifier'.format(self._name))

    @property
    def name(self):
        """The (unique) name/identifier for this signal."""
        return self._name

    @property
    def drive_name(self):
        """VHDL variable name to use for driving this signal."""
        if self.is_strobe:
            return 'intsigs_%s' % self._name
        return 'intsig_%s' % self._name

    @property
    def use_name(self):
        """VHDL variable name to use for reading this signal."""
        if self.is_strobe:
            return 'intsigr_%s' % self._name
        return 'intsig_%s' % self._name

    @property
    def width(self):
        """The vector width of this signal, or `None` if it is an
        `std_logic`."""
        return self._width

    @property
    def driver(self):
        """The driver for this signal. If this is `None`, no driver has been
        assigned yet. A driver can be assigned exactly once by assigning this
        property."""
        return self._driver

    @driver.setter
    def driver(self, driver):
        assert driver is not None
        if self._driver is not None:
            raise ValueError('multiple drivers for signal %s: %s and %s' % (
                self._name, self._driver, driver))
        self._driver = driver

    @property
    def is_strobe(self):
        """Whether or not this signal is a strobe signal."""
        return bool(self._strobers)

    def add_user(self, user):
        """Adds a user for this signal."""
        self._users.append(user)

    def add_strober(self, strober):
        """Adds a strober for this signal."""
        self._strobers.append(strober)

    def check_width(self, user, width=None):
        """Checks that the width of this signal is as expected."""
        if self._width is None and width is not None:
            raise ValueError(
                '%s expected signal %s to be a vector of width %d, but found '
                'an std_logic' % (user, self._name, width))
        if self._width is not None and width is None:
            raise ValueError(
                '%s expected signal %s to be an std_logic, but found a vector '
                'of width %d' % (user, self._name, self._width))
        if self._width != width:
            raise ValueError(
                '%s expected signal %s to be a vector of width %d, but found '
                'a vector of width %d' % (user, self._name, width, self._width))

    def check_consistency(self):
        """Checks consistency for this signal. Signals must have exactly one
        driver and one or more users to be consistent. Raises an appropriate
        error if the check fails, otherwise returns `None`."""
        if self._driver is None and not self._strobers:
            raise ValueError('signal %s does not have a driver' % self._name)
        if self._driver is not None and self._strobers:
            raise ValueError('signal %s has both a level driver and a strobe driver' % self._name)
        if not self._users:
            raise ValueError('signal %s is never used' % self._name)
