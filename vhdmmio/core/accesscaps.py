"""Module for `AccessCapabilities` and `ReadWriteCapabilities` objects."""

class AccessCapabilities:
    """Class maintaining flags indicating the capabilities of a field for
    a specific operation (read or write)."""

    def __init__(self, volatile=False, can_block=False, can_defer=False):
        super().__init__()
        self._volatile = bool(volatile)
        self._can_block = bool(can_block)
        self._can_defer = bool(can_defer)

    @property
    def volatile(self):
        """Returns whether there is a functional difference between performing
        the same exact operation on this field once or twice. Volatile fields
        cannot be combined with blocking fields within the same register."""
        return self._volatile

    @property
    def can_block(self):
        """Returns whether accessing this field can cause the bus to stall.
        Blocking fields cannot be combined with other blocking fields or
        volatile fields within the same register."""
        return self._can_block

    @property
    def can_defer(self):
        """Returns whether accesses to this field can be deferred = whether
        multiple outstanding requests are supported = whether the request
        pipeline can advance before the response is returned. Fields that have
        this flag set must be the only field within a register."""
        return self._can_defer

    @classmethod
    def check_siblings(cls, siblings):
        """Checks for incompatibilities between the given iterable of fields
        within a register. Returns the combined capabilities of the fields,
        or `None` if an empty list is supplied."""
        siblings = list(siblings)
        if not siblings:
            return None
        if len(siblings) >= 2 and any(map(lambda x: x.can_defer, siblings)):
            raise ValueError(
                'fields that can defer cannot be combined with other fields')
        if sum(map(lambda x: 1 if x.can_block else 0, siblings)) >= 2:
            raise ValueError(
                'fields that can block cannot be combined with other fields that can block')
        if (any(map(lambda x: x.can_block, siblings))
                and any(map(lambda x: x.volatile and not x.can_block, siblings))):
            raise ValueError(
                'blocking fields cannot be combined with volatile fields')
        return cls(
            volatile=any(map(lambda x: x.volatile, siblings)),
            can_block=any(map(lambda x: x.can_block, siblings)),
            can_defer=any(map(lambda x: x.can_defer, siblings)))

class ReadWriteCapabilities:
    """Base class for representing a field, register, or some other entity with
    read and/or write capabilities."""

    def __init__(self, read_caps=None, write_caps=None, **kwargs):
        """Constructs a new object with read and/or write capabilities."""
        super().__init__(**kwargs)

        if read_caps is None and write_caps is None:
            raise ValueError('read_caps and write_caps cannot both be None')

        if read_caps is not None and not isinstance(read_caps, AccessCapabilities):
            raise TypeError('read_caps must be None or be of type AccessCapabilities')
        self._read_caps = read_caps

        if write_caps is not None and not isinstance(write_caps, AccessCapabilities):
            raise TypeError('write_caps must be None or be of type AccessCapabilities')
        self._write_caps = write_caps

    @property
    def read_caps(self):
        """Returns the read capabilities of this field, or `None` if this field
        is write-only."""
        return self._read_caps

    @property
    def write_caps(self):
        """Returns the write capabilities of this field, or `None` if this
        field is read-only."""
        return self._write_caps

    def get_caps(self, write):
        """Returns the capabilities of this field for reading (`!write`) or
        writing (`write`). `None` is used to indicate that the operation is not
        supported."""
        return self.write_caps if write else self.read_caps
