"""Module for `Field` objects."""

from .metadata import ExpandedMetadata
from .bitrange import BitRange
from .fielddesc import FieldDescriptor
from .fieldlogic import FieldLogic
from .register import Register

class Field:
    """Represents a single field."""

    def __init__(self, meta, bitrange, logic, descriptor, index, register=None):
        """Constructs a new field.

         - `meta` is the expanded metadata/documentation for this field.
         - `bitrange` is the address of the field.
         - `logic` points to an object deriving from `FieldLogic`, describing
           the logic needed to construct the field in hardware.
         - `descriptor` points to the `FieldDescriptor` that describes this
           field.
         - `index` is the index of this field within the parent `FieldDescriptor`.
         - `register`, if specified, points to the `Register` that contains this
           field. If not specified, it can be assigned later.
        """
        super().__init__()

        if not isinstance(meta, ExpandedMetadata):
            raise TypeError('meta must be of type ExpandedMetadata')
        self._meta = meta

        if not isinstance(bitrange, BitRange):
            raise TypeError('bitrange must be of type BitRange')
        self._bitrange = bitrange

        if not isinstance(logic, FieldLogic):
            raise TypeError('logic must be of type FieldLogic')
        self._logic = logic

        if not isinstance(descriptor, FieldDescriptor):
            raise TypeError('descriptor must be of type FieldDescriptor')
        self._descriptor = descriptor
        if index is None:
            self._index = None
        else:
            self._index = int(index)

        if register is not None and not isinstance(register, Register):
            raise TypeError('register must be None or be of type Register')
        self._register = register

    @property
    def meta(self):
        """Field metadata."""
        return self._meta

    @property
    def bitrange(self):
        """Field address and bitrange."""
        return self._bitrange

    @property
    def logic(self):
        """Field logic descriptor."""
        return self._logic

    @property
    def descriptor(self):
        """Field descriptor."""
        return self._descriptor

    @property
    def index(self):
        """Field index within an array of fields, if any."""
        return self._index

    @property
    def register(self):
        """The register associated to this field, or `None` if it has not been
        mapped to a register yet."""
        if self._register is None:
            raise ValueError('this field does not a register assigned to it yet')
        return self._register

    @register.setter
    def register(self, register):
        if not isinstance(register, Register):
            raise TypeError('register must be of type Register')
        if self._register is not None:
            raise ValueError('this field already has a register assigned to it')
        self._register = register

    def is_array(self):
        """Returns whether this field is a scalar or an array. Fields are
        implicitly arrays when they have two or more entries and scalar when
        there is only one."""
        return len(self.descriptor) > 1

    def __str__(self):
        return self.meta.name
