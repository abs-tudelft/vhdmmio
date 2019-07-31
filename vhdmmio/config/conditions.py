"""Submodule for `ConditionConfig` configurable."""

import re
from ..configurable import configurable, Configurable, choice, required_choice

@configurable(name='Additional address match conditions')
class ConditionConfig(Configurable):
    """To support disabling registers at runtime and paged/indirect register
    files, `vhdmmio` allows you to specify additional conditions for the
    address matching logic of each register. This may be useful when not
    enough address space is allocated to the register file to fit all the
    registers, or when you want to emulate legacy register files such as a
    16550 UART."""

    #pylint: disable=E0211,E0213,E0202

    @required_choice
    def internal():
        """This key specifies the internal signal to use for the match
        condition."""
        yield (re.compile('[a-zA-Za-z][a-zA-Z0-9_]*'), 'a scalar internal '
               'with the given name is used for the match condition.')
        yield (re.compile('[a-zA-Za-z][a-zA-Z0-9_]*:[0-9]+'), 'a vector '
               'internal with the given name and width is used for the match '
               'condition.')

    @choice
    def value():
        """This key specifies the value that the signal must have for the
        logical register to be addressed."""
        yield False, 'the signal value needs to be 0.'
        yield True, 'the signal value needs to be 1.'
        yield int, 'the signal value needs to match the specified value.'

    @choice
    def ignore():
        """This key specifies the value that the signal must have for the
        logical register to be addressed."""
        yield 0, 'all bits must match.'
        yield (int, 'the bits set in this value are ignored when matching '
               'against `value`.')
