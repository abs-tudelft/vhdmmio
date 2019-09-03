"""Submodule for handling everything related to address matching/bitmasking and
paging."""

from collections import namedtuple, OrderedDict
from .mixins import Shaped, Named, Unique

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

    @staticmethod
    def _parse_str_cfg(value, full_mask, default_mask):
        """Helper for `parse_config()`, called when the value is a string."""

        # Handle mask suffix syntax.
        if '/' in value:
            value, size = value.split('/')
            mask = -1 << int(size)
        elif '|' in value:
            value, ignore = value.split('|')
            mask = ~int(ignore, 0)
        elif '&' in value:
            value, mask = value.split('&')
            mask = int(mask, 0)
        else:
            mask = default_mask

        # Handle hexadecimal numbers with don't cares.
        if value.startswith('0x'):
            value = value[2:]
            parsed_value = 0
            parsed_mask = full_mask
            while value:
                if value[0] == '-':
                    parsed_value <<= 4
                    parsed_mask <<= 4
                    value = value[1:]
                elif value[0] == '[':
                    for idx in range(1, 5):
                        parsed_value <<= 1
                        parsed_mask <<= 1
                        if value[idx] == '1':
                            parsed_value |= 1
                            parsed_mask |= 1
                        elif value[idx] == '0':
                            parsed_mask |= 1
                        else:
                            assert value[idx] == '-'
                    assert value[5] == ']'
                    value = value[6:]
                elif value[0] != '_':
                    parsed_value <<= 4
                    parsed_mask <<= 4
                    parsed_value |= int(value[0], 16)
                    parsed_mask |= 15
                    value = value[1:]
            return parsed_value, mask & parsed_mask

        # Handle binary numbers with don't cares.
        if value.startswith('0b'):
            value = value[2:]
            parsed_value = 0
            parsed_mask = full_mask
            while value:
                if value[0] == '_':
                    continue
                parsed_value <<= 1
                parsed_mask <<= 1
                if value[0] == '1':
                    parsed_value |= 1
                    parsed_mask |= 1
                elif value[0] == '0':
                    parsed_mask |= 1
                else:
                    assert value[0] == '-'
                value = value[1:]
            return parsed_value, mask & parsed_mask

        # Handle decimal numbers.
        return int(value), mask

    @classmethod
    def parse_config(cls, value, ignore_lsbs=0, signal_width=32):
        """Parses the `field.address` and `condition.value` configuration key
        syntax into a `MaskedAddress`. `ignore_lsbs` specifies the number of LSBs
        that are ignored by default. `signal_width` specifies the width of the
        signal, needed for the `ignore` syntax."""
        full_mask = (1 << signal_width) - 1
        default_mask = full_mask & (-1 << ignore_lsbs)

        # Handle values that have already been parsed by YAML.
        if value is False:
            return cls(0, full_mask)
        if value is True:
            return cls(1, full_mask)
        if isinstance(value, int):
            mask = default_mask
        else:
            value, mask = cls._parse_str_cfg(value, full_mask, default_mask)

        # Check range.
        if value & ~full_mask:
            raise ValueError('address 0x%X is out of range for %d bits' % (
                value, signal_width))

        # Post-process to make the mask and value valid for the given signal
        # width.
        mask &= full_mask
        value &= mask

        return cls(value, mask)

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

    def __add__(self, value):
        """Adds a number to the non-masked bits in the address."""
        address = self.address
        carry = 0
        for bit in range(self.mask.bit_length()):
            bitm = 1 << bit
            if not self.mask & bitm:
                continue
            in_bit = value & 1
            value >>= 1
            in_bits_set = in_bit + carry + bool(address & bitm)
            if (in_bits_set & 1) ^ bool(address & bitm):
                address ^= bitm
            carry = in_bits_set >> 1
        if value == 0:
            if carry:
                raise ValueError('overflow during address addition')
        elif value == -1:
            if not carry:
                raise ValueError('underflow during address addition')
        else:
            raise ValueError('address summand out of range')
        return MaskedAddress(address, self.mask)

    def __mul__(self, other):
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

    class _BusAddress(Named, Shaped, Unique):
        """Singleton class representing the incoming AXI4L bus address. The
        singleton to use is `AddressSignalMap.BUS`."""

        def __init__(self):
            super().__init__(name='address', shape=32)

    BUS = _BusAddress()

    def __init__(self):
        super().__init__()
        self._frozen = False

        # Ordered mapping from `Shaped+Named+Unique` objects to the offset of
        # the signal within the internal address.
        self._signals = OrderedDict()

        self._width = 0
        self._add_signal(self.BUS)

    @property
    def width(self):
        """Returns the width of the internal address signal."""
        return self._width

    def __iter__(self):
        """Iterates over the components of the internal address signal by
        yielding `(signal, offset)` tuples in insertion order = LSB to MSB."""
        return iter(self._signals.items())

    def _add_signal(self, address_signal):
        """Adds an address signal represented as a `Shaped+Named+Unique` object
        to this mapping. No-op if the signal is already mapped."""

        # If the signal is already in the map, this is no-op.
        if address_signal in self._signals:
            return

        # Can't add signals once frozen.
        if self._frozen:
            raise ValueError('address signal %s was not added during '
                             'register file construction' % address_signal)

        # Calculate the new width of the internal address signal.
        new_width = self._width + address_signal.width

        # Add the signal to the map and update the width.
        self._signals[address_signal] = self._width
        self._width = new_width

    def construct_address(self, mapping):
        """Constructs a `MaskedAddress` for the internal address structured as
        defined by this `AddressSignalMap` based on the requirements in
        `mapping`, which should be a mapping object from `Shaped+Named+Unique`
        signal objects to `MaskedAddress` objects. If a signal object is not
        part of the internal address yet, it is added automatically."""
        address = ALL_ADDRESSES
        for signal, sub_address in sorted(mapping.items(), key=lambda x: x[0].name):
            self._add_signal(signal)
            offset = self._signals[signal]
            address *= (sub_address & ((1 << signal.width) - 1)) << offset
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

    def freeze(self):
        """Shields this object against further mutation."""
        self._frozen = True

    def doc_represent_address(self, address):
        """Represents a `MaskedAddress` abiding by the structure defined by
        this object for use within markdown documentation."""
        doc_components = []
        for signal, sub_address in self.split_address(address).items():
            value = sub_address.doc_represent(signal.width)
            if signal is self.BUS:
                doc_components.append(value)
            elif value != '-':
                doc_components.append('`%s`=%s' % (signal.name, value))
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

    def __contains__(self, address):
        return address in self._map

    def __iter__(self):
        return iter(self._map)

    def items(self):
        """Chains to `dict.items()`."""
        return self._map.items()

    def get(self, *args, **kwargs):
        """Chains to `dict.get()`."""
        return self._map.get(*args, **kwargs)

    def pop(self, *args, **kwargs):
        """Chains to `dict.pop()`."""
        return self._map.pop(*args, **kwargs)


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

    def construct(self, resources, address, conditions):
        """Constructs an internal address from the given `MaskedAddress` for
        the incoming bus address, a list of `ConditionConfig` objects, and a
        `Resources` object to get the internal signal objects from."""
        subaddresses = {AddressSignalMap.BUS: address}
        for condition in conditions:
            internal = resources.internals.use(
                'address matching', condition.internal)
            value = MaskedAddress.parse_config(
                condition.value, signal_width=internal.width)
            subaddresses[internal] = value
        return self.signals.construct_address(subaddresses)

    def _raise_map_conflict(self, mode, exc, mapping):
        """Raises the exception for a conflict error."""
        raise ValueError(
            'address conflict between %s (%s) and %s (%s) at %s in %s mode' % (
                mapping,
                self.signals.doc_represent_address(exc.address_a),
                getattr(self, mode)[exc.address_b],
                self.signals.doc_represent_address(exc.address_b),
                self.signals.doc_represent_address(MaskedAddress(
                    exc.address_a.common(exc.address_b),
                    (1 << self.signals.width) - 1)),
                mode))

    def read_map(self, internal_address, constructor, *args, **kwargs):
        """Returns the current read mapping for `internal_address`, or
        constructs the mapping by calling `constructor(*args, **kwargs)` if
        there is no mapping yet. If this new mapping conflicts with existing
        mappings, an exception is raised."""
        mapping = self.read.get(internal_address, None)
        if mapping is None:
            mapping = constructor(*args, **kwargs)
            try:
                self.read[internal_address] = mapping
            except AddressConflictError as exc:
                self._raise_map_conflict('read', exc, mapping)
        return mapping

    def read_set(self, internal_address, mapping):
        """Like `read_map()`, but always sets the mapping to the specified
        object. If there was already an object at this address, a conflict
        error is issued."""
        old = self.read.get(internal_address, None)
        if old is not None:
            raise ValueError(
                'address conflict between %s and %s at %s in read mode' % (
                    mapping, old, self.signals.doc_represent_address(internal_address)))
        return self.read_map(internal_address, lambda: mapping)

    def write_map(self, internal_address, constructor, *args, **kwargs):
        """Returns the current write mapping for `internal_address`, or
        constructs the mapping by calling `constructor(*args, **kwargs)` if
        there is no mapping yet. If this new mapping conflicts with existing
        mappings, an exception is raised."""
        mapping = self.write.get(internal_address, None)
        if mapping is None:
            mapping = constructor(*args, **kwargs)
            try:
                self.write[internal_address] = mapping
            except AddressConflictError as exc:
                self._raise_map_conflict('write', exc, mapping)
        return mapping

    def write_set(self, internal_address, mapping):
        """Like `write_map()`, but always sets the mapping to the specified
        object. If there was already an object at this address, a conflict
        error is issued."""
        old = self.write.get(internal_address, None)
        if old is not None:
            raise ValueError(
                'address conflict between %s and %s at %s in write mode' % (
                    mapping, old, self.signals.doc_represent_address(internal_address)))
        return self.write_map(internal_address, lambda: mapping)

    def _natural_iter(self):
        """Iterates over the addresses in this address manager in natural
        order."""

        # Get the set of all addresses.
        addresses = set(self.read) | set(self.write)

        # Order the addresses in a natural way, where the bus address is major
        # to the paging signals. Unfortunately this is not the sorting order of
        # the `MaskedAddress` tuples themselves.
        addresses = [(self.signals.split_address(address), address) for address in addresses]
        addresses.sort(key=lambda x: tuple(x[0].values()))

        return iter(addresses)

    def __iter__(self):
        return map(lambda x: x[1], self._natural_iter())

    def doc_iter(self):
        """Iterates over the addresses and mapped objects in this address
        manager in a natural order for documentation output. The elements are
        yielded as `(subaddresses, address_repr, read_ob, write_ob)` tuples,
        where `address_repr` is a human-readable string representation of the
        address, and `read_ob`/`write_ob` are `None` if the address range is
        write-only/read-only."""

        # Iterate over the addresses, gathering additional information as we
        # go.
        for subaddresses, address in self._natural_iter():
            address_repr = self.signals.doc_represent_address(address)
            read_ob = self.read.get(address, None)
            write_ob = self.write.get(address, None)
            yield subaddresses, address_repr, read_ob, write_ob

    def doc_represent_address(self, address):
        """Formats documentation for the given internal address. Returns a
        tuple of the formatted address and a list of string representations of
        any additional match conditions."""
        bus_address = None
        conditions = []
        for signal, subaddress in self.signals.split_address(address).items():
            subaddress = subaddress.doc_represent(signal.width)
            if signal is AddressSignalMap.BUS:
                bus_address = subaddress
            elif subaddress != '-':
                conditions.append('%s=%s' % (signal.name, subaddress))
        return bus_address, conditions
