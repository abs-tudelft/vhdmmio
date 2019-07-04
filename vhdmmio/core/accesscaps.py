"""Module for `AccessCapabilities` and `ReadWriteCapabilities` objects."""

from enum import Enum

class NoOpMethod(Enum):
    """Enumeration of the possible minimum "effort" needed to make an access
    to this field no-op. This information is used when a neighboring field
    (i.e. in the same register) is to be accessed without affecting this
    field.

     - `ALWAYS` means that the access is always no-op.
     - `WRITE_ZERO` means that writing zero is no-op.
     - `WRITE_CURRENT_OR_MASK` means that a read-modify-write or the write
       strobe bits can be used for masking this field.
     - `WRITE_CURRENT` means that only read-modify-write can be used to mask
       this field (i.e. it ignores byte strobes).
     - `MASK` means that only the write strobe bits can be used to mask this
       field.
     - `NEVER` means that it is impossible to access the surrounding
       register without touching this field.
    """
    ALWAYS = 0
    WRITE_ZERO = 1
    WRITE_CURRENT_OR_MASK = 3
    WRITE_CURRENT = 2
    MASK = 4
    NEVER = 5


class AccessCapabilities:
    """Class maintaining flags indicating the capabilities of a field for
    a specific operation (read or write)."""

    def __init__(
            self,
            volatile=False, can_block=False, can_defer=False,
            no_op_method=NoOpMethod.NEVER, can_read_for_rmw=True):
        super().__init__()
        self._volatile = bool(volatile)
        self._can_block = bool(can_block)
        self._can_defer = bool(can_defer)
        self._no_op_method = no_op_method
        self._can_read_for_rmw = can_read_for_rmw

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

    @property
    def no_op_method(self):
        """Returns the no-op/masking method."""
        return self._no_op_method

    @property
    def can_read_for_rmw(self):
        """Returns whether this field can be read for the purpose of doing a
        read-modify-write."""
        return self._can_read_for_rmw

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

    @property
    def read_is_no_op(self):
        """Returns whether reading this field does not have any side
        effects."""
        return (
            self._read_caps is None
            or self._read_caps.no_op_method == NoOpMethod.ALWAYS)

    @property
    def masking_needed(self):
        """Returns whether masking writes to this field (i.e. behaving like the
        field isn't being accessed even though the surrounding register is)
        requires some action to be taken."""
        return (
            self._write_caps is not None
            and self._write_caps.no_op_method != NoOpMethod.ALWAYS)

    @property
    def can_mask_with_strobe(self):
        """Returns whether it is possible to mask out this field in a write
        access using the strobe bits."""
        return not self.masking_needed or self._write_caps.no_op_method not in (
            NoOpMethod.WRITE_CURRENT, NoOpMethod.NEVER)

    @property
    def can_mask_with_zero(self):
        """Returns whether it is possible to mask out this field in a write
        access by writing zeros."""
        return not self.masking_needed or self._write_caps.no_op_method in (
            NoOpMethod.WRITE_ZERO, NoOpMethod.ALWAYS)

    @property
    def can_mask_with_rmw(self):
        """Returns whether it is possible to mask out this field in a write
        access by using a read-modify-write (assuming that the field can be
        read)."""
        return (
            (not self.masking_needed or self._write_caps.no_op_method in (
                NoOpMethod.WRITE_CURRENT_OR_MASK, NoOpMethod.WRITE_CURRENT, NoOpMethod.ALWAYS))
            and self._read_caps is not None
            and self._read_caps.no_op_method == NoOpMethod.ALWAYS
            and self._read_caps.can_read_for_rmw)
