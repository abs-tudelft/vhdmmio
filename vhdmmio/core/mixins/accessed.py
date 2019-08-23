"""Submodule for the `Accessed` mixin."""

class Accessed:
    """Mixin for objects which are accessed by a bus. Stores whether the object
    is readable and/or writable."""

    def __init__(self, mode=None, **kwargs):
        super().__init__(**kwargs)
        assert 'R' in mode or 'W' in mode
        self._mode = mode

    @property
    def mode(self):
        """Returns the mode of this register: `'R/O'`, `'W/O'`, or `'R/W'`."""
        return self._mode

    def can_read(self):
        """Returns whether this register is readable."""
        return 'R' in self._mode

    def can_write(self):
        """Returns whether this register is writable."""
        return 'W' in self._mode
