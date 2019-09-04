"""Submodule for dealing with subaddresses."""

from collections import OrderedDict, namedtuple
from ..config import SubAddressConfig
from .mixins import Shaped
from .bitrange import BitRange

class SubAddress(Shaped):
    """Represents a subaddress, used for one or more fields."""

    BLANK = namedtuple('BLANK', ['target'])
    ADDRESS = namedtuple('ADDRESS', ['target', 'source'])
    INTERNAL = namedtuple('INTERNAL', ['target', 'source', 'internal'])

    def __init__(self, resources, field_descriptor, cfg, offset):
        # Handle default subaddress construction from the masked bits in the
        # incoming address.
        if not cfg:
            bus_width = field_descriptor.regfile.cfg.features.bus_width
            ignore_lsbs = bus_width.bit_length() - 4
            mask = field_descriptor.base_address.mask

            # Figure out the consecutive ranges of masked bits.
            start = None
            ranges = []
            for idx in range(ignore_lsbs, 32):
                bit = 1 << idx
                if mask & bit:
                    if start is not None:
                        ranges.append((start, idx - 1))
                        start = None
                elif start is None:
                    start = idx
            if start is not None:
                ranges.append((start, 31))

            # Construct the default configuration from that.
            if not ranges:
                cfg = [SubAddressConfig(blank=1)]
            else:
                cfg = []
                for start, end in ranges:
                    if end == start + 1:
                        cfg.append(SubAddressConfig(
                            address=start))
                    else:
                        cfg.append(SubAddressConfig(
                            address='%d..%d' % (end, start)))

        # Construct the components from the configuration.
        width = 0
        components = []
        for component_cfg in cfg:
            component = []
            internal_bitrange = component_cfg.internal_bitrange

            # Handle bus address components.
            if component_cfg.address is not None:
                source = BitRange.parse_config(component_cfg.address, 32)
                target = BitRange(width)
                if source.is_vector():
                    target = BitRange(width + source.width - 1, width)
                component.append(self.ADDRESS(target, source))

            # Handle internal signal components.
            if component_cfg.internal is not None:
                internal = resources.internals.use(
                    'subaddress', component_cfg.internal)
                source = None
                target = BitRange(width)
                if internal.is_vector():
                    source = BitRange.parse_config(
                        internal_bitrange, internal.width)
                    internal_bitrange = None
                    if source.is_vector():
                        target = BitRange(width + source.width - 1, width)
                component.append(self.INTERNAL(target, source, internal))

            # Handle blank/filler components.
            if component_cfg.blank is not None:
                if component_cfg.blank == 1: #pylint: disable=W0143
                    component.append(self.BLANK(BitRange(width)))
                else:
                    component.append(self.BLANK(
                        BitRange(width + component_cfg.blank - 1, width)))

            # Check for configuration errors.
            if internal_bitrange is not None:
                raise ValueError(
                    'the `internal-bitrange` key for a subaddress component '
                    'is only applicable for internal vector signals')
            if len(component) != 1:
                raise ValueError(
                    'exactly one of the `address`, `internal`, and `blank` '
                    'keys must be specified for each subaddress component')
            component = component[0]

            width += component.target.width
            components.append(component)

        # Reverse the components to place them in MSB to LSB order, and put
        # them in a tuple for immutability.
        components = tuple(reversed(components))

        self._components = components
        self._offset = offset
        self._name = None
        super().__init__(shape=width)

    @property
    def components(self):
        """The components that form the subaddress as a tuple in MSB to LSB
        order."""
        return self._components

    @property
    def offset(self):
        """The constant offset added to the subaddress after concatenation."""
        return self._offset

    @property
    def name(self):
        """Name for this subaddress signal. Note that the name is intentionally
        NOT part of the equality check; this allows equivalent subaddresses to
        be merged into a single signal/variable with a single name."""
        assert self._name is not None
        return self._name

    @name.setter
    def name(self, value):
        assert self._name is None
        self._name = value

    def __hash__(self):
        return hash((self.components, self.offset))

    def __eq__(self, other):
        return (
            isinstance(other, SubAddress) and
            self.components == other.components and
            self.offset == other.offset)


class SubAddressManager:
    """Storage for all subaddresses constructed so far. Subaddresses are
    uniquified, so only one signal/variable is created for equal subaddresses;
    this prevents a subaddress variable from being created for each field."""

    def __init__(self):
        super().__init__()
        self._subaddresses = OrderedDict()

    def construct(self, resources, field_descriptor):
        """Constructs and returns the subaddress signal for the given field
        descriptor."""
        with field_descriptor.context:
            new_subaddress = SubAddress(
                resources, field_descriptor,
                field_descriptor.cfg.subaddress,
                field_descriptor.cfg.subaddress_offset)
            subaddress = self._subaddresses.get(new_subaddress, None)
            if subaddress is None:
                subaddress = new_subaddress
                trivial = (len(subaddress.components) == 1
                           and isinstance(subaddress.components[0], SubAddress.BLANK)
                           and not subaddress.offset)
                if trivial:
                    subaddress.name = 'subaddr_none'
                else:
                    subaddress.name = 'subaddr_%s_etc' % field_descriptor.name
                self._subaddresses[subaddress] = subaddress
            return subaddress

    def __iter__(self):
        return iter(self._subaddresses)
