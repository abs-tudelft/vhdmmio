"""Module for `BitRange` object."""

from collections import namedtuple
from functools import total_ordering
import re

@total_ordering
class BitRange:
    """Represents a bitrange."""

    Mapping = namedtuple('Mapping', [
        'address', 'mask', 'bus_hi', 'bus_lo', 'field_hi', 'field_lo'])

    def __init__(self, bus_width, address, *args):
        """Constructs a bitrange.

         - `bus_width`: must be 32 or 64 bits.
         - `address`: the base byte address that the bit indices are relative to.
         - `size`: the rightshift to apply to the byte address
         - `*args`: if no extra arguments are specified, the field encompasses
           exactly one bus word. If one argument is specified, it is
           interpreted as a bit index with respect to the LSB of `address` that
           is mapped to a single `std_logic`-style field. If two arguments are
           specified, they are interpreted as the high and low bit of an
           `std_logic_vector`-style field; the order does not matter.
        """
        self._bus_width = int(bus_width)
        if self._bus_width not in (32, 64):
            raise ValueError('invalid bus width')

        self._address = int(address)
        if self._address < 0 or self._address > 0xFFFFFFFF:
            raise ValueError('address out of 32-bit range')

        min_size = {32: 2, 64: 3}[self._bus_width]
        self._size = min_size
        if len(args) >= 1 and args[0] is not None:
            self._size = int(args[0])
        if self._size < min_size or self._size > self._bus_width:
            raise ValueError('invalid block size')

        if self._address & (2**self._size - 1):
            raise ValueError('address is not aligned to block size')

        self._low_bit = 0
        self._high_bit = self._bus_width - 1
        if len(args) >= 3:
            self._low_bit = min(args[1:3])
            self._high_bit = max(args[1:3])
        elif len(args) == 2:
            self._low_bit = int(args[1])
            self._high_bit = None

        if self._low_bit < 0:
            raise ValueError('negative bit index')
        assert self._high_bit is None or self._high_bit >= self._low_bit

    @classmethod
    def from_spec(cls, bus_width, spec):
        """Parses an address block specification string or integer.

        The `spec` string syntax is:
         - The base address, in decimal, 0x<hex>, 0b<binary> or 0<octal>;
         - An optional size, indicated as a slash followed by the number of
           ignored byte address bits (so 2 would be 32-bit, 3 would be 64-bit,
           etc.). If not specified, the size is set to the bus width.
         - An optional bitrange, separated using a colon. The bitrange must
           either be a single bit index for `std_logic`-type fields, or an
           inclusive descending range using `..` to separate the upper and
           lower bits for `std_logic_vector`-type fields. If not specified,
           the range is set to the size of a single register.

        `bus_width` must be 32 or 64 (same as the constructor).
        """
        if isinstance(spec, int):
            return cls(bus_width, int(spec))

        match = re.match((
            r'([1-9][0-9]*|0x[a-fA-F0-9]+|0b[01]+|0o?[0-7]*)?'
            r'(?:/([1-9][0-9]*|0))?'
            r'(?::([1-9][0-9]*|0)(?:\.\.([1-9][0-9]*|0))?)?$'
        ), str(spec))
        if not match:
            raise ValueError('failed to parse address specification {}'.format(repr(spec)))

        address = match.group(1)
        if not address:
            address = 0
        elif address.startswith('0') and not (
                address.startswith('0b') or address.startswith('0x')):
            address = int(address, 8)
        else:
            address = int(address, 0)

        size = match.group(2)
        if size is not None:
            size = int(size)

        args = []
        for i in range(2):
            if match.group(3+i) is not None:
                args.append(int(match.group(3+i)))

        return cls(bus_width, address, size, *args)

    def to_spec(self):
        """Inverse of `from_spec()`."""
        if self.size == {32:2, 64:3}[self.bus_width]:
            addr = '0x{:08X}'.format(self.address)
        else:
            addr = '0x{:08X}/{:d}'.format(self.address, self.size)
        if self.is_word():
            return addr
        if self.is_vector():
            return addr + ':{:d}..{:d}'.format(self.high_bit, self.low_bit)
        return addr + ':{:d}'.format(self.low_bit)

    def move(self, address_offset=0, bit_offset=0):
        """Returns a new BitRange by shifting its position by the given
        offsets."""
        if self.is_vector():
            return BitRange(
                self.bus_width,
                self.address + address_offset,
                self.size,
                self.high_bit + bit_offset,
                self.low_bit + bit_offset)
        return BitRange(
            self.bus_width,
            self.address + address_offset,
            self.size,
            self.low_bit + bit_offset)

    @property
    def bus_width(self):
        """This bus width that this range was configured for."""
        return self._bus_width

    @property
    def address(self):
        """This base address for this range."""
        return self._address

    @property
    def size(self):
        """The number of LSB address bits to ignore in the address (block
        size)."""
        return self._size

    @property
    def low_bit(self):
        """The low bit index with respect to the base address."""
        return self._low_bit

    @property
    def high_bit(self):
        """The high bit index with respect to the base address."""
        return self._high_bit if self._high_bit is not None else self._low_bit

    @property
    def width(self):
        """The size of the field in bits."""
        return self.high_bit - self.low_bit + 1

    @property
    def xwidth(self):
        """The size of the field in bits if it is a vector, `None` otherwise."""
        if self.is_vector():
            return self.width
        return None

    def is_vector(self):
        """Whether this field is to be implemented as a `std_logic_vector` or
        an `std_logic`."""
        return self._high_bit is not None

    def is_word(self):
        """Whether this field encompasses exactly one bus word."""
        return self.low_bit == 0 and self.high_bit == self.bus_width - 1

    def __iter__(self):
        """Yields `Mapping` objects in ascending address order."""
        addr = self.address
        incr = 2**self.size
        mask = ~(incr - 1)
        offs = 0
        while True:
            bus_hi = min(self.bus_width - 1, self.high_bit - offs)
            bus_lo = max(0, self.low_bit - offs)
            if bus_hi < 0:
                break
            if bus_hi >= bus_lo:
                field_hi = bus_hi + offs - self.low_bit
                field_lo = bus_lo + offs - self.low_bit
                yield self.Mapping(addr, mask, bus_hi, bus_lo, field_hi, field_lo)
            offs += self.bus_width
            addr += incr

    def __len__(self):
        return len(list(self.__iter__()))

    def __lt__(self, other):
        return (isinstance(other, BitRange) and
                (self.address, self.low_bit, self.xwidth) <
                (other.address, other.low_bit, self.xwidth))

    def __eq__(self, other):
        return (
            isinstance(other, BitRange)
            and self.address == other.address
            and self.size == other.size
            and self.low_bit == other.low_bit
            and self.xwidth == other.xwidth
            and self.bus_width == other.bus_width)

    def __str__(self):
        return self.to_spec()

    def __repr__(self):
        if not self.is_vector():
            fmt = '{}({:d}, 0x{:08X}, {:d}, {:d})'
        elif not self.is_word():
            fmt = '{}({:d}, 0x{:08X}, {:d}, {:d}, {:d})'
        elif self.size == {32: 2, 64: 3}[self.bus_width]:
            fmt = '{}({:d}, 0x{:08X})'
        else:
            fmt = '{}({:d}, 0x{:08X}, {:d})'
        return fmt.format(
            type(self).__name__, self.bus_width,
            self.address, self.size, self.high_bit, self.low_bit)

    def __hash__(self):
        return self.address * self._bus_width + self.low_bit
