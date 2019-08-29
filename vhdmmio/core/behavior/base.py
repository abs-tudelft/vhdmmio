"""Contains the base class for behaviors."""

from enum import Enum
from ..mixins import Configured

_BEHAVIOR_CLASS_MAP = []


def behavior(config_cls):
    """Decorator generator which registers a behavior class."""
    def decorator(behavior_cls):
        _BEHAVIOR_CLASS_MAP.append((config_cls, behavior_cls))
        return behavior_cls
    return decorator


class BusAccessNoOpMethod(Enum):
    """Enumeration of the minimum "effort" needed to make an access to the
    associated field no-op. This information is used when a different field in
    the same register is to be accessed without affecting this field.
    Read-write fields need two of these, one for read accesses and one for
    write accesses. For reads, only `ALWAYS` and `NEVER` are sensible.

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
    WRITE_CURRENT = 2
    WRITE_CURRENT_OR_MASK = 3
    MASK = 4
    NEVER = 5


class BusAccessBehavior:
    """This class describes the features of a field's bus interface for a read
    or write access for as far as the behavior-agnostic hardware and software
    layers can use the field, or ignore it when a different field in the same
    register is to be accessed."""

    def __init__(self, permission_cfg,
                 volatile=False, blocking=False, deferring=False,
                 no_op_method=BusAccessNoOpMethod.NEVER):
        super().__init__()
        self._volatile = volatile
        self._blocking = blocking
        self._deferring = deferring
        self._no_op_method = no_op_method

        permission_cfg.freeze()

        # `prot` bit 2.
        if permission_cfg.data and permission_cfg.instruction:
            prot_mask = '-'
        elif permission_cfg.data:
            prot_mask = '0'
        elif permission_cfg.instruction:
            prot_mask = '1'
        else:
            raise ValueError('cannot deny both data and instruction accesses')

        # `prot` bit 1.
        if permission_cfg.secure and permission_cfg.nonsecure:
            prot_mask += '-'
        elif permission_cfg.secure:
            prot_mask += '0'
        elif permission_cfg.nonsecure:
            prot_mask += '1'
        else:
            raise ValueError('cannot deny both secure and nonsecure accesses')

        # `prot` bit 0.
        if permission_cfg.user and permission_cfg.privileged:
            prot_mask += '-'
        elif permission_cfg.user:
            prot_mask += '0'
        elif permission_cfg.privileged:
            prot_mask += '1'
        else:
            raise ValueError('cannot deny both user and privileged accesses')

        self._permission_cfg = permission_cfg
        self._prot_mask = prot_mask

    @property
    def volatile(self):
        """Whether there is a functional difference between performing
        the same exact operation on this field once or twice. Volatile fields
        cannot be combined with blocking fields within the same register."""
        return self._volatile

    @property
    def blocking(self):
        """Whether accessing this field can cause the bus to stall.
        Blocking fields cannot be combined with other blocking fields or
        volatile fields within the same register."""
        return self._blocking

    @property
    def deferring(self):
        """Whether accesses to this field can be deferred = whether
        multiple outstanding requests are supported = whether the request
        pipeline can advance before the response is returned. Fields that have
        this flag set must be the only field within a register."""
        return self._deferring

    @property
    def no_op_method(self):
        """Returns the no-op/masking method, i.e., the method that is to be
        used to not cause side effects to this field when a different field in
        the same register is to be accessed, if any."""
        return self._no_op_method

    @property
    def permission_cfg(self):
        """The frozen `PermissionConfig` object used to construct the
        permissions for this behavior."""
        return self._permission_cfg

    @property
    def prot_mask(self):
        """The `prot` bitmask that must match for an access to be allowed
        within the context of these permissions."""
        return self._prot_mask

    def is_protected(self):
        """Returns whether any access types are denied."""
        return self.prot_mask != '---'


class BusBehavior:
    """This class describes the featurs of a field's bus interface for both
    read and write access, thus containing one or two `BusAccessBehavior`s
    depending on whether the field is read-only/write-only or read-write."""

    def __init__(self, read=None, write=None, can_read_for_rmw=True):
        super().__init__()
        if read is None and write is None:
            raise ValueError('must support either or both read and write mode')
        if read is not None and read.no_op_method not in (
                BusAccessNoOpMethod.ALWAYS, BusAccessNoOpMethod.NEVER):
            raise ValueError('read no-op method must be ALWAYS or NEVER')
        self._read = read
        self._write = write
        self._can_read_for_rmw = can_read_for_rmw

    @property
    def read(self):
        """The read behavior for this field, or `None` if the field is
        write-only."""
        return self._read

    @property
    def write(self):
        """The write behavior for this field, or `None` if the field is
        read-only."""
        return self._write

    def can_read(self):
        """Returns whether this field is readable."""
        return self.read is not None

    def can_write(self):
        """Returns whether this field is writable."""
        return self.write is not None

    def is_read_no_op(self):
        """Returns whether reading this field does not have any side
        effects."""
        return (
            not self.can_read()
            or self.read.no_op_method == BusAccessNoOpMethod.ALWAYS)

    def is_write_no_op(self):
        """Returns whether writing this field does not have any (side)
        effects."""
        return (
            not self.can_write()
            or self.write.no_op_method == BusAccessNoOpMethod.ALWAYS)

    def can_mask_with_strobe(self):
        """Returns whether it is possible to mask out this field in a write
        access using the strobe bits."""
        return self.is_write_no_op() or (
            self.write.no_op_method in (
                BusAccessNoOpMethod.WRITE_ZERO,
                BusAccessNoOpMethod.WRITE_CURRENT_OR_MASK,
                BusAccessNoOpMethod.MASK))

    def can_mask_with_zero(self):
        """Returns whether it is possible to mask out this field in a write
        access by writing zeros."""
        return self.is_write_no_op() or (
            self.write.no_op_method == BusAccessNoOpMethod.WRITE_ZERO)

    def can_mask_with_rmw(self):
        """Returns whether it is possible to mask out this field in a write
        access by using a read-modify-write (assuming that the field can be
        read)."""
        return self.is_write_no_op() or (
            self.write.no_op_method in (
                BusAccessNoOpMethod.WRITE_CURRENT_OR_MASK,
                BusAccessNoOpMethod.WRITE_CURRENT)
            and self.can_read()
            and self.read.no_op_method == BusAccessNoOpMethod.ALWAYS
            and self._can_read_for_rmw)

    def is_protected(self):
        """Returns whether any access types are denied based on the `a*_prot`
        fields."""
        return (
            (self.can_read() and self.read.is_protected())
            or (self.can_write() and self.write.is_protected()))


class Behavior(Configured):
    """Base class for field behaviors."""

    def __init__(self, field_descriptor, behavior_cfg, bus_behavior):
        super().__init__(cfg=behavior_cfg)
        self._field_descriptor = field_descriptor
        self._bus = bus_behavior

    @staticmethod
    def construct(resources, field_descriptor, behavior_cfg, read_allow_cfg, write_allow_cfg):
        """Constructs a `Behavior` class instance based on the given configuration
        structures and a reference to the associated field."""
        for config_cls, behavior_cls in _BEHAVIOR_CLASS_MAP:
            if isinstance(behavior_cfg, config_cls):
                return behavior_cls(
                    resources, field_descriptor, behavior_cfg, read_allow_cfg, write_allow_cfg)
        raise TypeError(
            'no mapping exists from type %s to a Behavior subclass'
            % type(behavior_cfg).__name__)

    @property
    def field_descriptor(self):
        """The field descriptor that this behavior object is representing."""
        return self._field_descriptor

    @property
    def bus(self):
        """The behavior of the bus for this field."""
        return self._bus

    @property
    def doc_reset(self):
        """The reset value as printed in the documentation as an integer, or
        `None` if the field is driven by a signal and thus does not have a
        register to reset."""
        return None
