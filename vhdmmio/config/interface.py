"""Submodule for `InterfaceConfig` configurable."""

import re
from ..configurable import configurable, Configurable, choice

@configurable(name='VHDL interface configuration')
class InterfaceConfig(Configurable):
    """Each field and interrupt in `vhdmmio` can register scalar and vector
    inputs and outputs, as well as generics. This configuration structure
    determines how these interfaces are exposed in the entity.

    By default, the ports are grouped by field/interrupt into records while
    generics are flattened, but either can be overridden. It is also possible
    to group multiple fields/interrupts together in a single record."""
    #pylint: disable=E0211,E0213

    @choice
    def group():
        """Name of the group record used for ports, if any. The ports for any
        objects that share the same non-null `group` tag are combined into a
        single record pair (`in` and `out`)."""
        yield None, 'port grouping is determined by the global default.'
        yield False, 'ports are not grouped in an additional record.'
        yield (re.compile(r'[a-zA-Z][a-zA-Z0-9_]*'),
               'ports are grouped in a record with the specified name.')

    @choice
    def flatten():
        """Whether the ports for this object should be flattened or combined in
        a record (pair)."""
        yield None, 'port flattening is determined by the global default.'
        yield (False, 'all ports needed for this object are combined in a '
               'record specific to the object. If `group` is specified in '
               'addition, there will be two levels of records. For arrays, '
               'an array of records is created.')
        yield ('record', 'The record mentioned above is flattened out. For '
               'array objects, `std_logic` ports become `std_logic_array`s '
               '(ascending range), and `std_logic_vector` ports become an '
               'array (ascending range) of an appropriately sized '
               '`std_logic_vector`.')
        yield (True, 'All port types are flattened to `std_logic`s or '
               '`std_logic_vector`s. `std_logic_vector` ports for array '
               'objects are simply concatenated using the customary '
               'descending range, with the lowest-indexed field in the '
               'least-significant position.')

    @choice
    def generic_group():
        """Same as `group`, but for generics."""
        yield None, 'generic grouping is determined by the global default.'
        yield False, 'generics are not grouped in an additional record.'
        yield (re.compile(r'[a-zA-Z][a-zA-Z0-9_]*'),
               'generics are grouped in a record with the specified name.')

    @choice
    def generic_flatten():
        """Same as `flatten`, but for generics."""
        yield None, 'generic flattening is determined by the global default.'
        yield ('record', 'generics are not grouped in a record, but arrays '
               'remain regular arrays (possibly of `std_logic_vector`s).')
        yield (True, 'as above, but all `std_logic`-based generics are '
               'flattened to single `std_logic`s or std_logic_vector`s. '
               'Other primitive types still receive their own custom array '
               'type for array objects.')
        yield (False, 'all generics needed for this object are combined in a '
               'record specific to the object.')
