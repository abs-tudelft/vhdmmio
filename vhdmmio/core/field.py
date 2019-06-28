"""Module for `Field`, `FieldDescriptor`, and `FieldLogic` objects."""

from .metadata import Metadata, ExpandedMetadata
from .bitrange import BitRange
from .register import Register
from .logic import FieldLogic
from ..vhdl.interface import InterfaceOptions

class FieldDescriptor:
    """Class representing the description of a field or an array of fields, as
    described in a single node of the YAML file."""

    def __init__(self, regfile, **kwargs):
        """Constructs a field descriptor from its YAML dictionary
        representation."""
        self._regfile = regfile

        # Parse metadata.
        self._meta = Metadata.from_dict(1, kwargs.copy())
        try:

            # Parse address.
            address = kwargs.pop('address', None)
            if isinstance(address, list):
                self._field_repeat = None
                self._stride = None
                self._field_stride = None
                self._bitranges = [BitRange.from_spec(regfile.bus_width, spec) for spec in address]
                if not self._bitranges:
                    raise ValueError('at least one address must be specified')
                if any(key in kwargs for key in [
                        'repeat', 'field_repeat', 'stride', 'field_stride']):
                    raise ValueError('cannot combine automatic repetition with multiple addresses')
                self._vector_width = self._bitranges[0].xwidth
                for bitrange in self._bitranges[1:]:
                    if bitrange.xwidth != self._vector_width:
                        raise ValueError('repeated fields must all have the same width')
                self._vector_count = len(self._bitranges)

            elif isinstance(address, (str, int)):
                base = BitRange.from_spec(regfile.bus_width, address)
                if 'repeat' in kwargs:
                    repeat = int(kwargs.pop('repeat', 1))
                    if repeat < 1:
                        raise ValueError('repeat must be positive')
                    field_repeat = kwargs.pop('field_repeat', None)
                    if field_repeat is None:
                        field_repeat = repeat
                    else:
                        field_repeat = int(field_repeat)
                    if field_repeat < 1:
                        raise ValueError('field-repeat must be positive')
                    stride = int(kwargs.pop('stride', 2**base.size))
                    if abs(stride) < 2**base.size:
                        raise ValueError('stride is smaller than the block size')
                    if stride & (2**base.size-1):
                        raise ValueError('stride is not aligned to the block size')
                    field_stride = int(kwargs.pop('field_stride', base.width))
                    if abs(field_stride) < base.width:
                        raise ValueError('field-stride is smaller than the width of a single field')

                    self._field_repeat = field_repeat
                    self._stride = stride
                    self._field_stride = field_stride
                    self._bitranges = [base.move(
                        (index // field_repeat) * stride,
                        (index % field_repeat) * field_stride)
                                       for index in range(repeat)]
                    self._vector_width = base.xwidth
                    self._vector_count = repeat
                else:
                    self._field_repeat = None
                    self._stride = None
                    self._field_stride = None
                    self._bitranges = [base]
                    self._vector_width = base.xwidth
                    self._vector_count = None
            else:
                raise ValueError('invalid or missing address')

            # Parse metadata again, now with the correct repetition count.
            self._meta = Metadata.from_dict(self._vector_count, kwargs)
            if any(('register_' + key in kwargs for key in ('mnemonic', 'name', 'brief', 'doc'))):
                self._reg_meta = Metadata.from_dict(self._vector_count, kwargs, 'register_')
            else:
                self._reg_meta = None

            # Parse type information.
            self._logic = FieldLogic.from_dict(self, kwargs)

            # Collect the fields described by this descriptor.
            if self._vector_count is None:
                self._fields = (
                    Field(self._meta[None], self._bitranges[0], self._logic, self, None),)
            else:
                self._fields = tuple((
                    Field(self._meta[index], self._bitranges[index], self._logic, self, index)
                    for index in range(self._vector_count)))

            # Parse interface options.
            iface_opts = kwargs.pop('interface', None)
            if iface_opts is None:
                iface_opts = {}
            self._iface_opts = InterfaceOptions.from_dict(iface_opts)

            # Check for unknown keys.
            for key in kwargs:
                raise ValueError('unexpected key in field description: %s' % key)

        except (ValueError, TypeError) as exc:
            raise type(exc)('while parsing field %s: %s' % (self._meta.name, exc))

    @classmethod
    def from_dict(cls, regfile, dictionary):
        """Constructs a field descriptor object from a dictionary."""
        dictionary = dictionary.copy()
        for key in list(dictionary.keys()):
            if '-' in key:
                dictionary[key.replace('-', '_')] = dictionary.pop(key)
        return cls(regfile, **dictionary)

    def to_dict(self, dictionary=None):
        """Returns a dictionary representation of this object."""
        if dictionary is None:
            dictionary = {}

        # Write address.
        base = self._bitranges[0]
        if len(self._bitranges) == 1:
            dictionary['address'] = base.to_spec()
        elif self._field_repeat is None:
            dictionary['address'] = [address.to_spec() for address in self._bitranges]
        else:
            dictionary['address'] = base.to_spec()
            dictionary['repeat'] = len(self._bitranges)
            if self._field_repeat != len(self._bitranges):
                dictionary['field-repeat'] = self._field_repeat
            if self._stride != 2**base.size:
                dictionary['stride'] = self._stride
            if self._field_stride != base.width:
                dictionary['field-stride'] = self._field_stride

        # Write metadata.
        self._meta.to_dict(dictionary)
        if self._reg_meta is not None:
            self._reg_meta.to_dict(dictionary, 'register-')

        # Write type information.
        self._logic.to_dict(dictionary)

        # Write interface options.
        iface = self._iface_opts.to_dict()
        if iface:
            dictionary['interface'] = iface

        return dictionary

    @property
    def meta(self):
        """Metadata for this group of fields."""
        return self._meta

    @property
    def reg_meta(self):
        """Metadata for the surrounding register, if any."""
        return self._reg_meta

    @property
    def vector_width(self):
        """Size of each field described by this array in bits, or `None` if the
        fields are single-bit."""
        return self._vector_width

    @property
    def vector_count(self):
        """Number of fields described by this descriptor if it describes an
        array, or `None` if this is a scalar field."""
        return self._vector_count

    @property
    def logic(self):
        """Object logic description."""
        return self._logic

    @property
    def iface_opts(self):
        """Returns an `InterfaceOptions` object, carrying the options for
        generating the VHDL interface for this group of fields."""
        return self._iface_opts

    @property
    def regfile(self):
        """Register file that this field is bound to."""
        return self._regfile

    @property
    def fields(self):
        """Collection of fields described by this descriptor."""
        return self._fields

    def __hash__(self):
        return hash(self.meta.name)

    def __eq__(self, other):
        return self is other

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

        assert isinstance(meta, ExpandedMetadata)
        self._meta = meta

        assert isinstance(bitrange, BitRange)
        self._bitrange = bitrange

        assert isinstance(logic, FieldLogic)
        self._logic = logic

        assert isinstance(descriptor, FieldDescriptor)
        self._descriptor = descriptor
        if index is None:
            self._index = None
        else:
            self._index = int(index)

        assert register is None or isinstance(register, Register)
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
        assert self._register is not None
        return self._register

    @register.setter
    def register(self, register):
        assert isinstance(register, Register)
        assert self._register is None
        self._register = register

    def is_array(self):
        """Returns whether this field is a scalar or an array. Fields are
        implicitly arrays when they have two or more entries and scalar when
        there is only one."""
        return len(self.descriptor) > 1

    def __str__(self):
        return self.meta.name

    def __hash__(self):
        return hash(self.meta.name)

    def __eq__(self, other):
        return self is other
