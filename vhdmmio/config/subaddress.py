"""Submodule for `SubAddressConfig` configurable."""

import re
from ..configurable import configurable, Configurable, choice

@configurable(name='Subaddress components')
class SubAddressConfig(Configurable):
    """`vhdmmio` fields can encompass more than one address. This allows fields
    such as memories and AXI passthrough to exist. Accessing such a field
    involves an address in addition to the read and write data. This address is
    called a subaddress. This configuration structure specifies part of a
    custom subaddress format.

    Note that exactly one of the `address`, `internal`, and `blank` keys must
    be specified."""

    #pylint: disable=E0211,E0213,E0202

    @choice
    def address():
        """This key specifies that this component of the subaddress is based on
        bits taken from the incoming address. Normally these bits would be
        masked out, but this is not required."""
        yield (None, 'this subaddress component is not based on the incoming '
               'address.')
        yield (0, 31), 'the specified bit of the incoming address is used.'
        yield ((re.compile(r'[0-9]+\.\.[0-9]+'), '`<high>..<low>`'),
               'the specified bitrange of the incoming address is used. The '
               'range is inclusive, so the number of bits in the subaddress '
               'component is `<high>` - `<low>` + 1.')

    @choice
    def internal():
        """This key specifies that this component of the subaddress is based
        on the value of an internal signal."""
        yield (None, 'this subaddress component is not based on an internal '
               'signal.')
        yield (re.compile(r'[a-zA-Za-z][a-zA-Z0-9_]*'), 'a scalar internal '
               'with the given name is inserted into the subaddress at the '
               'current position.')
        yield (re.compile(r'[a-zA-Za-z][a-zA-Z0-9_]*:[0-9]+'), 'a vector '
               'internal with the given name and width is inserted into the '
               'subaddress at the current position.')

    @choice
    def internal_bitrange():
        """For component based on vector internal signals, this key allows you
        to use only a subset of the signal for this component. In conjunction
        with other subaddress components based on the same signal, this allows
        bits to be reordered."""
        yield None, 'the entire vector is used.'
        yield (0, None), 'only the specified bit within the vector is used.'
        yield ((re.compile(r'[0-9]+\.\.[0-9]+'), '`<high>..<low>`'),
               'the specified subset of the vector is used. The range is '
               'inclusive, so the number of bits in the subaddress component '
               'is `<high>` - `<low>` + 1.')
    @choice
    def blank():
        """This key specifies that a number of blank bits should be inserted as
        the next component. The bits are always zero; use the
        `subaddress-offset` key in the field descriptor to set a different
        value."""
        yield (None, 'this subaddress component is not a blank.')
        yield ((1, None), 'the specified number of blank (zero) bits are '
               'inserted.')
