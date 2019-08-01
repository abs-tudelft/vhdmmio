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
        int_re = r'(0x[0-9A-Fa-f]+|0b[01]+|[0-9]+)'
        dc_int_re = r'(0x([-0-9A-Fa-f]|\[[-01]{4}\])+|0b[-01]+|[0-9]+)'
        yield False, 'the signal value needs to be 0.'
        yield True, 'the signal value needs to be 1.'
        yield (0, None), 'the signal needs to have the specified value.'
        yield ((re.compile(dc_int_re), 'a hex/bin integer with don\'t cares'),
               'the signal value is matched against the given number, '
               'specified as a string representation of a hexadecimal or '
               'binary integer which may contain don\'t cares (`-`). In '
               'hexadecimal integers, bit-granular don\'t-cares can be '
               'specified by inserting four-bit binary blocks enclosed in '
               'square braces in place of a hex digit.')
        yield ((re.compile(dc_int_re + r'/[0-9]+'), '`<address>/<size>`'),
               'as before, but the given number of LSBs are ignored in '
               'addition.')
        yield ((re.compile(int_re + r'\|' + int_re), '`<address>|<ignore>`'),
               'specifies the required signal value and ignored bits using '
               'two integers. Both integers can be specified in hexadecimal, '
               'binary, or decimal. A bit which is set in the `<ignore>` '
               'value is ignored in the matching process.')
        yield ((re.compile(int_re + r'\&' + int_re), '`<address>&<mask>`'),
               'specifies the required signal value and bitmask using two '
               'integers. Both integers can be specified in hexadecimal, '
               'binary, or decimal. A bit which is not set in the `<ignore>` '
               'value is ignored in the matching process.')
