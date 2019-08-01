"""Submodule for handling bitranges."""

from functools import total_ordering
from .mixins import Shaped

@total_ordering
class BitRange(Shaped):
    """Represents a range of bits within a register or number."""

    def __init__(self, high_bit, low_bit=None, **kwargs):
        assert high_bit >= 0
        if low_bit is None:
            super().__init__(shape=None, **kwargs)
            self._high_bit = high_bit
            self._low_bit = high_bit
        else:
            assert high_bit >= low_bit
            assert low_bit >= 0
            super().__init__(shape=high_bit - low_bit + 1, **kwargs)
            self._high_bit = high_bit
            self._low_bit = low_bit

    @property
    def high_bit(self):
        """The high_bit bit index."""
        return self._high_bit

    @property
    def low_bit(self):
        """The low_bit bit index."""
        return self._low_bit

    @property
    def index(self):
        """Asserts that bitrange is scalar and returns the bit index."""
        assert self.is_scalar()
        return self._low_bit

    @classmethod
    def parse_config(cls, value, bus_width):
        """Parses the `field.bitrange` configuration key syntax into a
        `BitRange`. `bus_width` specifies the width of the bus, used when the
        bitrange is omitted from the configuration."""

        # Handle default.
        if value is None:
            return cls(bus_width - 1, 0)

        # Handle scalar bitrange notation.
        if isinstance(int, value):
            return cls(value)

        # Handle vector bitrange notation.
        high_bit, low_bit = value.split('..')
        return cls(int(high_bit), int(low_bit))

    def __lshift__(self, value):
        """Shifts the bitrange left."""
        if self.is_vector():
            return BitRange(self.high_bit + value, self.low_bit + value)
        return BitRange(self.index + value)

    def __rshift__(self, value):
        """Shifts the bitrange right."""
        if self.is_vector():
            return BitRange(self.high_bit - value, self.low_bit - value)
        return BitRange(self.index - value)

    def __eq__(self, other):
        if not isinstance(other, BitRange):
            return False
        return self.low_bit == other.low_bit and self.shape == other.shape

    def __le__(self, other):
        if not isinstance(other, BitRange):
            raise TypeError()
        return (
            (self.low_bit, self.is_vector(), self.width)
            < (other.low_bit, other.is_vector(), other.width))

    def __hash__(self):
        return hash((self.low_bit, self.shape))

    def __str__(self):
        if self.is_vector():
            return '%d..%d' % (self.high_bit, self.low_bit)
        return '%d' % self.index

    def __repr__(self):
        if self.is_vector():
            return 'Bitrange(%d, %d)' % (self.high_bit, self.low_bit)
        return 'Bitrange(%d)' % self.index
