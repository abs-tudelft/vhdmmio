"""Temporary test code for configurable stuff."""

import re
from vhdmmio.core.bitrange import BitRange
from . import configurable, Configurable, ParseError, choice, flag, parsed, embedded, opt_embedded

@configurable()
class Metadata(Configurable):
    """Metadata for the surrounding object."""
    #pylint: disable=E0211,E0213

    def __init__(self, parent):
        self._parent = parent
        if self.name is None and self.mnemonic is None:
            raise ParseError('name and mnemonic cannot both be auto-generated')
        print(self.name, self.mnemonic)

    @choice
    def mnemonic():
        """The mnemonic of the object."""
        yield None, 'the mnemonic is auto-generated.'
        yield re.compile(r'[A-Z][A-Z0-9_]*'), 'the mnemonic.'

    @choice
    def name():
        """The name of the object."""
        yield None, 'the name is auto-generated.'
        yield re.compile(r'[a-zA-Z_][a-zA-Z0-9_]*'), 'the name.'

@configurable(name='register file')
class Test(Configurable):
    """Hello."""
    #pylint: disable=E0211,E0213

    def __init__(self):
        pass

    @flag
    def test_flag():
        """Flag used for testing the configuration system."""

    @choice
    def bus_width():
        """Width of the bus in bits."""
        yield 32, 'the register file is accessed through a 32-bit AXI-lite bus.'
        yield 64, 'the register file is accessed through a 64-bit AXI-lite bus.'

    @parsed
    def bitrange(self, value):
        """Bitrange test!"""
        return BitRange.from_spec(self.bus_width, value)

    @bitrange.serializer
    def bitrange(value):
        """Serializer for `bitrange`."""
        return BitRange.to_spec(value)

    @embedded
    def meta():
        """Metadata for this object."""
        return Metadata

    @opt_embedded
    def reg_meta():
        """Metadata for the surrounding register."""
        return 'register', Metadata

print(Test.from_dict({'bitrange': 32, 'name': 'hello'}).to_dict())

print(Test.configuration_markdown())
