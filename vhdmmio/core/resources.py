"""Submodule classes that manage resources during the construction of a
register file. These classes are necessarily mutable since they track state,
but are ultimately private to the constructed register files."""

from .internal import InternalManager
from .address import AddressManager
from .subaddress import SubAddressManager

class Resources:
    """Class containing the resource managers used while constructing the
    register file. These are not part of `RegisterFile` itself, because they
    are private to the construction process."""

    def __init__(self):
        super().__init__()
        self._internals = InternalManager()
        self._addresses = AddressManager()
        self._subaddresses = SubAddressManager()

    @property
    def internals(self):
        """Resource manager for internal signals."""
        return self._internals

    @property
    def addresses(self):
        """Resource manager for the address decoder."""
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
