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
    def generate_vhdl(generator):
        """Generates the VHDL code for the associated field by updating the
        given `vhdl.Generator` object."""
        raise NotImplementedError('generate_vhdl() must be overridden')
