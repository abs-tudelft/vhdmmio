"""Constant field behaviors for reading the design-time configuration of the
hardware."""

from ...configurable import derive, checked, ParseError
from .registry import behavior, behavior_doc
from .primitive import ReadOnlyPrimitive

behavior_doc(
    'Constant fields for reading the design-time configuration of the '
    'hardware:', 1)

@behavior(
    'constant', 'field which always reads as the same constant value.', 2)
@derive(name='`constant` behavior')
class Constant(ReadOnlyPrimitive):
    """Fields with `constant` behavior always return the value specified
    through the `value` option when read. They cannot be written."""

    @checked
    def value(self, value):
        """Configures the value using an integer or boolean."""
        if not isinstance(value, int):
            ParseError.invalid('', value, 'an integer', 'a boolean')
        self.reset = value
        return value

@behavior(
    'config', 'field which always reads as the same value, configured through '
    'a generic.', 2)
@derive(name='`config` behavior', reset='generic')
class Config(ReadOnlyPrimitive):
    """Fields with `config` behavior always return the value specified by a
    VHDL generic. They cannot be written."""
