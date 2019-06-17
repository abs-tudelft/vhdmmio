"""Module for the `FieldLogic` base class."""

from .accesscaps import ReadWriteCapabilities
from .logic_registry import type_lookup

class FieldLogic(ReadWriteCapabilities):
    """Base class for representing the hardware description of this register
    and its interface to the user's logic."""

    _TYPE_CODE = None

    def __init__(self, field_descriptor=None, **kwargs):
        super().__init__(**kwargs)
        assert field_descriptor is not None
        self._field_descriptor = field_descriptor

    @staticmethod
    def from_dict(field_descriptor, dictionary):
        """Constructs a `FieldLogic` object from a dictionary. The key `'type'`
        is used to select the subclass to use."""
        typ = dictionary.pop('type', 'control')
        return type_lookup(typ)(field_descriptor, dictionary)

    def to_dict(self, dictionary):
        """Returns a dictionary representation of this object."""
        dictionary['type'] = self.type_code

    @property
    def type_code(self):
        """Returns the type code of this field."""
        return self._TYPE_CODE

    @property
    def field_descriptor(self):
        """The `FieldDescriptor` object associated with this object."""
        return self._field_descriptor

    @property
    def meta(self):
        """Metadata for this group of fields."""
        return self._field_descriptor.meta

    @property
    def vector_width(self):
        """Size of each field described by this array in bits, or `None` if the
        fields are single-bit."""
        return self._field_descriptor.vector_width

    @property
    def vector_count(self):
        """Number of fields described by this descriptor if it describes an
        array, or `None` if this is a scalar field."""
        return self._field_descriptor.vector_count

    @staticmethod
    def generate_vhdl_package():
        """Generates the VHDL code block that is placed in the package header,
        or returns `''` to indicate that no code is needed here."""
        return ''

    @staticmethod
    def generate_vhdl_package_body():
        """Generates the VHDL code block that is placed in the package body,
        or returns `''` to indicate that no code is needed here."""
        return ''

    @staticmethod
    def generate_vhdl_generics():
        """Generates the VHDL code block that is placed in the generic
        description of the entity/component, or returns `''` to indicate that
        no code is needed here."""
        return ''

    @staticmethod
    def generate_vhdl_ports():
        """Generates the VHDL code block that is placed in the port description
        of the entity/component, or returns `''` to indicate that no code is
        needed here."""
        return ''

    @staticmethod
    def generate_vhdl_variables():
        """Generates the VHDL code block that is placed in the process header,
        or returns `''` to indicate that no code is needed
        here."""
        return ''

    @staticmethod
    def generate_vhdl_before_bus():
        """Generates the VHDL code block that is executed every cycle *before*
        the bus logic, or returns `''` to indicate that no code is needed
        here."""
        return ''

    @staticmethod
    def generate_vhdl_read(index): #pylint: disable=W0613
        """Generates the VHDL code block that is executed when the field is
        read, or returns `''` to indicate that no code is needed here."""
        return ''

    @staticmethod
    def generate_vhdl_read_lookahead(index): #pylint: disable=W0613
        """Generates the VHDL code block that is executed when the field is
        going to be read but the result cannot be returned yet, or returns
        `''` to indicate that no code is needed here."""
        return ''

    @staticmethod
    def generate_vhdl_read_deferred(index): #pylint: disable=W0613
        """Generates the VHDL code block that is executed when the result of
        a previously deferred read can be returned, or returns `''` to
        indicate that no code is needed here."""
        return ''

    @staticmethod
    def generate_vhdl_write(index): #pylint: disable=W0613
        """Generates the VHDL code block that is executed when the field is
        written, or returns `''` to indicate that no code is needed here."""
        return ''

    @staticmethod
    def generate_vhdl_write_lookahead(index): #pylint: disable=W0613
        """Generates the VHDL code block that is executed when the field is
        going to be written but the result cannot be returned yet, or returns
        `''` to indicate that no code is needed here."""
        return ''

    @staticmethod
    def generate_vhdl_write_deferred(index): #pylint: disable=W0613
        """Generates the VHDL code block that is executed when the result of
        a previously deferred write can be returned, or returns `''` to
        indicate that no code is needed here."""
        return ''

    @staticmethod
    def generate_vhdl_after_bus():
        """Generates the VHDL code block that is executed every cycle *after*
        the bus logic, or returns `''` to indicate that no code is needed
        here."""
        return ''
