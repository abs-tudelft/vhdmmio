"""Submodule for handling everything related to address matching/bitmasking and
paging."""

from collections import namedtuple, OrderedDict
from .shaped import Shaped

class AddressSignal(Shaped):
    """Represents a signal that is mapped to one or more internal address
    bits. Intended to be subclassed based on the signal type, its origin, etc.
    Needed by the base class are a name for documentation and a shape."""

    def __init__(self, name, shape=None):
        super().__init__(shape=shape)
        self._name = name

    @property
    def name(self):
        """Name of the signal, mostly intended for the documentation output."""
        return self._name

    def __hash__(self):
        return id(self)

    def __eq__(self, other):
        return self is other

    def __ne__(self, other):
        return self is not other

    def __str__(self):
        return self.name

    def __repr__(self):
        return 'AddressSignal(%r, %r)' % (self.name, self.shape)

    def doc_represent(self, value):
        """Represents an address matching operation for this signal against the
        given representation of the to-be-matched value itself for usage in
        documentation output. The value is expected to be a string returned by
        `MaskedAddress.doc_represent()`. If the string is `'-'` (a don't care)
        `None` may be returned to suppress the match operation in the
        documentation, but subclasses may also choose to always output the
        match."""
        if value == '-':
            return None
        return '`%s`=%s' % (self._name, value)


_MaskedAddress = namedtuple('_MaskedAddress', ['address', 'mask'])

class MaskedAddress(_MaskedAddress):
    """Represents an address with a mask that addresses can be matched against.
    A MaskedAddress, like a Python int, can be arbitrarily large, but the
    number of bits that are considered in the match must be finite (i.e., mask
    must not be negative)."""

    def __new__(cls, *args, **kwargs):
        new = super(MaskedAddress, cls).__new__(cls, *args, **kwargs)
        if new.mask < 0:
            raise ValueError('cannot match an infinite amount of bits')
        return new

    def __contains__(self, address):
        """Returns whether the specified address is contained in the mask."""
        return (address & self.mask) == (self.address & self.mask)

    def contains_all(self):
        """Returns whether this `MaskedAddress` matches all addresses."""
        return self.mask == 0

    def common(self, other):
        """Returns an address that is contained by both this `MaskedAddress`
        and the given other `MaskedAddress`. Returns `None` if there is no such
        address. If multiple addresses satisfy the condition, this can return
        any one of them; it's primarily intended to be used as an example."""
        if self.mask & other.mask & (self.address ^ other.address):
            return None
        return (self.mask & self.address) | (other.mask & other.address)

    def __lshift__(self, shamt):
        """Shifts a mask left, shifting in don't cares."""
        return MaskedAddress(self.address << shamt, self.mask << shamt)

    def __rshift__(self, shamt):
        """Shifts a mask right, shifting in don't cares."""
        return MaskedAddress(self.address >> shamt, self.mask >> shamt)

    def __and__(self, mask):
        """Removes match conditions for the bits that are not set in the given
        integer mask."""
        return MaskedAddress(self.address & mask, self.mask & mask)

    def __add__(self, other):
        """Combines two addresses with non-overlapping masks. The result is a
        `MaskedAddress` that matches iff both incoming `MaskedAddress`es
        match."""
        if self.mask & other.mask:
            raise ValueError(
                'combining overlapping addresses is probably not what you want')
        return MaskedAddress(
            (self.address & self.mask) | (other.address & other.mask),
            self.mask | other.mask)

    def doc_represent(self, width):
        """Represents this address for documentation purposes. Tries to find
        the most human-readable representation of the value and mask. `width`
        must be set to the number of bits in the address for proper
        formatting."""

        # Get the address and mask, making sure that no bits beyond the given
        # bit width are set.
        width_mask = ((1 << width) - 1)
        address = self.address & width_mask
        mask = self.mask & width_mask
        inv_mask = ~self.mask & width_mask

        # Return a simple don't-care dash when all bits are masked out.
        if not mask:
            return '-'

        # Determine the format string for representing the address.
        if width <= 1:
            int_format = '%d'
        else:
            int_format = '0x%%0%dX' % ((width + 3) // 4)

        # If all bits are in the mask, simply return the formatted address.
        if mask == (1 << width) - 1:
            return int_format % address

        # If only a number of LSBs of the address are ignored, use the /
        # notation that we also use in bitranges.
        lsbs_ignored = int.bit_length(inv_mask)
        if inv_mask == (1 << lsbs_ignored) - 1:
            return '%s/%d' % (int_format % address, lsbs_ignored)

        # We have a nontrivial bitmask, so we need to print in binary using
        # don't-care dashes.
        bits = []
        for idx in reversed(range(width)):
            if not mask & (1 << idx):
                bits.append('-')
            elif address & (1 << idx):
                bits.append('1')
            else:
                bits.append('0')
        return '0b%s' % ''.join(bits)


ALL_ADDRESSES = MaskedAddress(0, 0)


class AddressSignalMap:
    """Stores how an internal address is built up from incoming signals. This
    is usually just the incoming address, but additional bits may be added at
    the MSB side for paging. The mapping always contains the special
    `AddressSignalMap.BUS` signal, which represents the incoming AXI4-lite bus
    address."""

    class _BusAddress(AddressSignal):
        """Singleton class representing the incoming AXI4L bus address. The
        singleton to use is `AddressSignalMap.BUS`."""

        def __init__(self):
            super().__init__('address', 32)

        def doc_represent(self, value):
            """Always represent match operations with the incoming address in the
            documentation. Furthermore, the name of the signal is implicit."""
            return value

    BUS = _BusAddress()

    def __init__(self):
        super().__init__()

        # Ordered mapping from AddressSignal object to the size of the
        # signal in bits, or None to indicate that the signal is scalar.
        self._signals = OrderedDict()
        self._width = 0
        self.append(self.BUS)

    @property
    def width(self):
        """Returns the width of the internal address signal."""
        return self._width

    def __iter__(self):
        """Iterates over the components of the internal address signal by
        yielding `(signal, offset)` tuples in insertion order = LSB to MSB."""
        return self._signals.items()

    def append(self, address_signal):
        """Adds an address signal to this mapping. No-op if the signal is
        already mapped."""

        # If the signal is already in the map, this is no-op.
        if address_signal in self._signals:
            return

        # Calculate the new width of the internal address signal.
        new_width = self._width + address_signal.width

        # Add the signal to the map and update the width.
        self._signals[address_signal] = self._width
        self._width = new_width

    def construct_address(self, mapping):
        """Constructs a `MaskedAddress` for the internal address structured as
        defined by this `AddressSignalMap` based on the requirements in
        `mapping`, which should be a mapping object from `AddressSignal`
        objects contained in this `AddressSignalMap` to `MaskedAddress`
        objects."""
        address = ALL_ADDRESSES
        for signal, sub_address in mapping.items():
            offset = self._signals[signal]
            address += (sub_address & ((1 << signal.width) - 1)) << offset
        return address

    def split_address(self, address):
        """The reverse of `construct_address()`. The mappings are returned as
        an `OrderedDict`, in the same order in which the signals were added to
        this `AddressSignalMap`. A mapping is returned even if the subaddress
        matches everything."""
        mappings = OrderedDict()
        for signal, offset in self._signals.items():
            sub_address = (address >> offset) & ((1 << signal.width) - 1)
            mappings[signal] = sub_address
        return mappings

    def doc_represent_address(self, address):
        """Represents a `MaskedAddress` abiding by the structure defined by
        this object for use within markdown documentation."""
        doc_components = []
        for signal, sub_address in self.split_address(address).items():
            doc_component = signal.doc_represent(sub_address.doc_represent(signal.width))
            if doc_component:
                doc_components.append(doc_component)
        return ', '.join(doc_components)


class AddressConflictError(ValueError):
    """Custom exception class for reporting address conflicts. The offending
    addresses can be retrieved from `address_a` and `address_b` to prettify the
    message after it's thrown."""
    def __init__(self, address_a, address_b):
        super().__init__('address conflict between %r and %r at 0x%X' % (
            address_a, address_b, address_a.common(address_b)))
        self.address_a = address_a
        self.address_b = address_b


class AddressMap:
    """Specialized mapping object for mapping `MaskedAddress`es to arbitrary
    Python objects (usually representing registers). The mapping object ensures
    that there are no address conflicts. Note that this is a rather costly
    operation, since in the worst case all exiting addresses need to be checked
    for conflicts with the new address."""

    def __init__(self):
        super().__init__()
        self._map = {}

    def __setitem__(self, address, value):
        """Adds an address to the mapping or updates the current value for an
        existing mapping."""

        # Handle updating an existing entry.
        if address in self._map:
            self._map[address] = value
            return

        # Check for conflicts.
        for other in self._map:
            if address.common(other) is not None:
                raise AddressConflictError(address, other)

        # Add the new mapping.
        self._map[address] = value

    def __getitem__(self, address):
        return self._map[address]

    def __delitem__(self, address):
        del self._map[address]

    def __iter__(self):
        return iter(self._map)

    def items(self):
        """Chains to `dict.items()`."""
        return self._map.items()

    def get(self, *args, **kwargs):
        """Chains to `dict.get()`."""
        return self._map.get(*args, **kwargs)


class AddressManager:
    """Manages an `AddressSignalMap` and two `AddressMap`s (one for read, one
    for write)."""

    def __init__(self):
        super().__init__()
        self._signals = AddressSignalMap()
        self._read = AddressMap()
        self._write = AddressMap()

    @property
    def signals(self):
        """The managed address signal map."""
        return self._signals

    @property
    def read(self):
        """The managed read address decoder map."""
        return self._read

    @property
    def write(self):
        """The managed write address decoder map."""
        return self._write

    def add_mapping(self, obj, bus_address, read=True, write=True, paging=None):
        """Adds a mapping for obj with the specified read/write mode."""
        subaddresses = {AddressSignalMap.BUS: bus_address}
        if paging is not None:
            subaddresses.update(paging)
        address = self.signals.construct_address(subaddresses)
        for enable, decoder, mode in ((read, self.read, 'read'), (write, self.write, 'write')):
            if not enable:
                continue
            try:
                decoder[address] = obj
            except AddressConflictError as exc:
                raise ValueError(
                    'address conflict between %s (%s) and %s (%s) at %s in %s mode' % (
                        obj, self.signals.doc_represent_address(exc.address_a),
                        decoder[exc.address_b], self.signals.doc_represent_address(exc.address_b),
                        self.signals.doc_represent_address(MaskedAddress(
                            exc.address_a.common(exc.address_b), (1 << self.signals.width) - 1)),
                        mode))

    def doc_iter(self):
        """Iterates over the addresses and mapped objects in this address
        manager in a natural order for documentation output. The elements are
        yielded as `(subaddresses, address_repr, read_ob, write_ob)` tuples,
        where `address_repr` is a human-readable string representation of the
        address, and `read_ob`/`write_ob` are `None` if the address range is
        write-only/read-only."""

        # Get the set of all addresses.
        addresses = set(self.read) | set(self.write)

        # Order the addresses in a natural way, where the bus address is major
        # to the paging signals. Unfortunately this is not the sorting order of
        # the `MaskedAddress` tuples themselves.
        addresses = [(self.signals.split_address(address), address) for address in addresses]
        addresses.sort(key=lambda x: tuple(x[0].values()))

        # Iterate over the addresses, gathering additional information as we
        # go.
        for subaddresses, address in addresses:
            address_repr = self.signals.doc_represent_address(address)
            read_ob = self.read.get(address, None)
            write_ob = self.write.get(address, None)
            yield subaddresses, address_repr, read_ob, write_ob
