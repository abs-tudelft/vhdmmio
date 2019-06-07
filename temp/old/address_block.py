"""Module for dealing with word/bit address blocks."""

import re
import functools

@functools.total_ordering
class BitRange:
    """Class representing the address and bit range of a field. Refer to the
    constructor docs for more info."""

    def __init__(self, bus_width, address, size, low_bit, high_bit=None):
        """Constructs a bit range.

        `bus_width` must be 32 or 64. `address` must be an integer between 0
        and 2^32. `size` must be set to the number of LSBs that are to be
        ignored when matching the incoming request address to the given
        address. `low_bit` must be set to LSB of the range with respect to the
        given address, which must be between 0 and the bus width. `high_bit`,
        if specified, specifies the MSB; if not specified, the range is a
        single scalar bit.

        The MSB can be greater than or equal to the bus width to define a field
        that occupies multiple registers, using little-endian ordering. This is
        called a wrapping range. Wrapping ranges cannot be combined with
        `size`s other than the native bus width, since the entire address must
        be matched to address the individual words."""
        super().__init__()

        # Check the bus width.
        self._bus_width = int(bus_width)
        if self._bus_width == 32:
            self._bus_size = 2
        elif self._bus_width == 64:
            self._bus_size = 3
        else:
            raise ValueError(
                'bus width ({}) must be 32 or 64'
                .format(bus_width))

        # Check low bit index.
        self._low_bit = int(low_bit)
        if self._low_bit < 0 or self._low_bit >= self._bus_width:
            raise ValueError(
                'low bit ({}) must be between 0 and the bus width (exclusive)'
                .format(self._low_bit))

        # Check high bit index. None means that this is a single-bit field
        # without using array notation, low = high means single-bit with
        # array notation.
        if high_bit is None:
            self._high_bit = None
            highest_bit = self._low_bit
        else:
            self._high_bit = int(high_bit)
            highest_bit = self._high_bit
            if self._high_bit < self._low_bit:
                raise ValueError(
                    'low bit ({}) must be <= high bit ({})'
                    .format(low_bit, high_bit))

        # Multi-register blocks and fields wrapping into the next register(s)
        # can not be mixed.
        if highest_bit >= self._bus_width:
            max_size = self._bus_size
        else:
            max_size = 31

        # Check the size.
        self._size = int(size)
        if self._size < self._bus_size or self._size > max_size:
            raise ValueError(
                'size ({}) must be between {} and {}'
                .format(size, self._bus_size, max_size))

        # Compute the address mask from the size.
        self._mask = -1 << self._size

        # Check the address.
        self._address = int(address) & self._mask
        if self._address < 0 or self._address > 0xFFFFFFFF:
            raise ValueError(
                'address ({}) must be between 0 and 0xFFFFFFFF'
                .format(address))

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
        default_size = 2 if bus_width == 32 else 3

        if isinstance(spec, int):
            address = int(spec)
            size = default_size
            high_bit = bus_width - 1
            low_bit = 0
        else:
            match = re.match((
                r'([1-9][0-9]*|0x[a-fA-F0-9]+|0b[01]+|0o?[0-7]*)'
                r'(?:/([1-9][0-9]*|0))?'
                r'(?::(?:([1-9][0-9]*|0)\.\.)([1-9][0-9]*|0))?$'
            ), str(spec))
            if not match:
                raise ValueError('failed to parse address specification {}'.format(repr(spec)))

            address = match.group(1)
            if address.startswith('0') and not (
                    address.startswith('0b') or address.startswith('0x')):
                address = int(address, 8)
            else:
                address = int(address, 0)

            size = match.group(2)
            if size is not None:
                size = int(size)
            else:
                size = default_size

            high_bit = match.group(3)
            if high_bit is not None:
                high_bit = int(high_bit)

            low_bit = match.group(4)
            if low_bit is not None:
                low_bit = int(low_bit)
            else:
                high_bit = bus_width - 1
                low_bit = 0

        return cls(bus_width, address, size, low_bit, high_bit)

    def to_spec(self):
        """Inverse of `from_spec()`."""
        if self._high_bit is None:
            return '0x{:X}/{:d}:{:d}'.format(
                self._address, self._size, self._low_bit)
        return '0x{:X}/{:d}:{:d}..{:d}'.format(
            self._address, self._size, self._high_bit, self._low_bit)

    @property
    def low_bit(self):
        """Returns the low bit index."""
        return self._low_bit

    @property
    def high_bit(self):
        """Returns the high bit index with respect to the base address
        register. This may be greater than the bus width; in this case, the
        field wraps over to subsequent registers using little-endian
        ordering."""
        if self._high_bit is not None:
            return self._high_bit
        return self._low_bit

    @property
    def bit_width(self):
        """Returns the bit-width of this field."""
        return self.high_bit - self.low_bit + 1

    def is_vector(self):
        """Returns whether this field is a scalar bit or a vector."""
        return self._high_bit is not None

    def is_multi_register(self):
        """Returns whether this field wraps into subsequent registers (in
        little-endian order)."""
        return self.high_bit >= self._bus_width

    @property
    def address(self):
        """The start of the block represented by this bitrange."""
        return self._address

    @property
    def last_byte_address(self):
        """The last byte address that's part of this block."""
        return (
            self._address
            + ~self._mask
            + (self.high_bit // self._bus_width) * (self._bus_width // 8))

    @property
    def address_mask(self):
        """The mask to be applied to the address before checking equality."""
        return self._mask

    def address_in_block(self, address):
        """Returns whether the given address maps to this range."""
        return (address & self._mask) == self._address

    def __iter__(self):
        """Returns a two-tuple of `AddressBlock`s and bit offsets for each word
        register captured by this block. The bit offsets should be added to the
        low/high bit indices of the resulting `AddressBlock`s to get the
        indices of the field bits that they're connected to (this is nonzero
        for wrapping registers)."""
        address_range = range(self.address, self.last_byte_address + 1, self._bus_width // 8)
        if self.is_multi_register():
            offset = 0
            for address in address_range:
                yield (offset, AddressBlock(
                    self._bus_width, address, self._bus_size,
                    max(self.low_bit - offset, 0),
                    min(self.high_bit - offset, self._bus_width - 1)))
                offset += self._bus_width
        else:
            for address in address_range:
                yield (0, AddressBlock(
                    self._bus_width, address, self._bus_size,
                    self._low_bit, self._high_bit))

    def __len__(self):
        """Returns the number of word addresses captured by this block."""
        return len(self.__iter__())

    def __lt__(self, other):
        return (
            isinstance(other, AddressBlock)
            and (self.address, self.low_bit) < (other.address, other.low_bit))

    def __eq__(self, other):
        return (
            isinstance(other, AddressBlock)
            and self.address == other.address
            and self.low_bit == other.low_bit
            and self.high_bit == other.high_bit
            and self.address_mask == other.address_mask)

    def __str__(self):
        return self.to_spec()

    def __repr__(self):
        if self._high_bit is None:
            return '{}({:d}, 0x{:X}, {:d}, {:d})'.format(
                type(self).__name__, self._bus_width,
                self._address, self._size, self._low_bit)
        return '{}({:d}, 0x{:X}, {:d}, {:d}, {:d})'.format(
            type(self).__name__, self._bus_width,
            self._address, self._size, self._low_bit, self._high_bit)

    def __hash__(self):
        return self.address * self._bus_width + self.low_bit
