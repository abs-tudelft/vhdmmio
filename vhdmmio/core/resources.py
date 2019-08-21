"""Submodule classes that manage resources during the construction of a
register file. These classes are necessarily mutable since they track state,
but are ultimately private to the constructed register files."""

from .internal import InternalManager
from .address import AddressManager
from .subaddress import SubAddressManager
from .defer_tag import DeferTagManager
from .interrupt import InterruptManager
from .namespace import Namespace

class Resources:
    """Class containing the resource managers used while constructing the
    register file. These are not part of `RegisterFile` itself, because they
    are private to the construction process."""

    def __init__(self, regfile):
        super().__init__()
        self._internals = InternalManager(regfile)
        self._addresses = AddressManager()
        self._block_addresses = AddressManager()
        self._subaddresses = SubAddressManager()
        self._read_tags = DeferTagManager()
        self._write_tags = DeferTagManager()
        self._interrupts = InterruptManager()
        self._descriptor_namespace = Namespace('field descriptor', check_mnemonics=False)
        self._register_namespace = Namespace('register')
        self._interrupt_namespace = Namespace('interrupt')

    @property
    def internals(self):
        """Resource manager for internal signals."""
        return self._internals

    @property
    def addresses(self):
        """Resource manager for checking address conflicts and recording which
        signals are used in the address match pass."""
        return self._addresses

    def construct_address(self, address, conditions):
        """Constructs an internal address from the given `MaskedAddress` for
        the incoming bus address and a list of `ConditionConfig` objects.
        Convenience method for `self.addresses.construct()`, which takes this
        object as an argument."""
        return self.addresses.construct(self, address, conditions)

    @property
    def subaddresses(self):
        """Resource manager for subaddress signals."""
        return self._subaddresses

    def construct_subaddress(self, field):
        """Constructs and returns the subaddress signal for the given field.
        Convenience method for `self.subaddresses.construct()`, which takes this
        object as an argument."""
        return self.subaddresses.construct(self, field)

    @property
    def read_tags(self):
        """The deferral tag manager for read accesses."""
        return self._read_tags

    @property
    def write_tags(self):
        """The deferral tag manager for write accesses."""
        return self._write_tags

    @property
    def interrupts(self):
        """The interrupt manager, used to connect interrupt fields to the
        interrupt objects themselves."""
        return self._interrupts

    @property
    def descriptor_namespace(self):
        """Namespace manager for field descriptors and fields."""
        return self._descriptor_namespace

    @property
    def register_namespace(self):
        """Namespace manager for logical registers and fields."""
        return self._register_namespace

    @property
    def interrupt_namespace(self):
        """Namespace manager for interrupts."""
        return self._interrupt_namespace

    def verify_and_freeze(self):
        """Performs post-construction checks, and prevents further mutation for
        some of the objects."""
        self.internals.verify_and_freeze()
        self.interrupts.verify()
        self.addresses.signals.freeze()
