"""Module for `FieldCapabilities` object."""

class FieldCapabilities:
    """Class maintaining flags indicating the capabilities of a field for
    either a specific operation (read or write)."""

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

    @staticmethod
    def check_siblings(siblings):
        """Checks for incompatibilities between the given iterable of fields
        within a register."""
        siblings = list(siblings)
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
