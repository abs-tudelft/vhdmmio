"""Submodule for handling bitranges."""

from functools import total_ordering
from .mixins import Shaped

@total_ordering
class BitRange(Shaped):
    """Represents a range of bits within a register or number."""

    def __init__(self, high, low=None, **kwargs):
        assert high >= 0
        if low is None:
            super().__init__(shape=None, **kwargs)
            self._high = high
            self._low = high
        else:
            assert high >= low
            assert low >= 0
            super().__init__(shape=high - low + 1, **kwargs)
            self._high = high
            self._low = low

    @property
    def high(self):
        """The high bit index."""
        return self._high

    @property
    def low(self):
        """The low bit index."""
        return self._low

    @property
    def index(self):
        """Asserts that bitrange is scalar and returns the bit index."""
        assert self.is_scalar()
        return self._low

    @classmethod
    def parse_config(cls, value, width, flexible=False):
        """Parses the `field.bitrange` configuration key syntax into a
        `BitRange`. `width` specifies the width of the signal, used when the
        bitrange is omitted from the configuration. Unless `flexible` is set,
        this is also limits the maximum bit index."""

        # Handle default.
        if value is None:
            return cls(width - 1, 0)

        # Handle scalar bitrange notation.
        if isinstance(value, int):
            if value >= width and not flexible:
                raise ValueError('bitrange index out of range')
            return cls(value)

        # Handle vector bitrange notation.
        high, low = value.split('..')
        high = int(high)
        low = int(low)
        if high >= width and not flexible:
            raise ValueError('bitrange index out of range')
        if low > high and not flexible:
            raise ValueError('bitranges should be descending')
        return cls(high, low)

    def __lshift__(self, value):
        """Shifts the bitrange left."""
        if self.low + value < 0:
            raise ValueError('bit index underflow while shifting bitrange')
        if self.is_vector():
            return BitRange(self.high + value, self.low + value)
        return BitRange(self.index + value)

    def __rshift__(self, value):
        """Shifts the bitrange right."""
        return self << -value

    def __eq__(self, other):
        if not isinstance(other, BitRange):
            return False
        return self.low == other.low and self.shape == other.shape

    def __le__(self, other):
        if not isinstance(other, BitRange):
            raise TypeError()
        return (
            (self.low, self.is_vector(), self.width)
            < (other.low, other.is_vector(), other.width))

    def __hash__(self):
        return hash((self.low, self.shape))

    def __str__(self):
        if self.is_vector():
            return '%d..%d' % (self.high, self.low)
        return '%d' % self.index

    def __repr__(self):
        if self.is_vector():
            return 'Bitrange(%d, %d)' % (self.high, self.low)
        return 'Bitrange(%d)' % self.index
