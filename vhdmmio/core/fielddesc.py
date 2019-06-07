"""Module for `FieldDescriptor` object."""

from .metadata import Metadata
from .bitrange import BitRange

class FieldDescriptor:

    def __init__(self, regfile, **kwargs):
        """Constructs a field descriptor from its YAML dictionary
        representation."""
        self._regfile = regfile

        # Parse address.
        address = kwargs.pop('address', None)
        if isinstance(address, list):
            self._field_repeat = None
            self._stride = None
            self._field_stride = None
            self._bitranges = [BitRange.from_spec(regfile.bus_width, spec) for spec in address]
            if not self._bitranges:
                raise ValueError('at least one address must be specified')
            if 'repeat' in kwargs:
                raise ValueError('cannot combine repeat with multiple addresses')
            if 'field_repeat' in kwargs:
                raise ValueError('cannot combine field-repeat with multiple addresses')
            if 'stride' in kwargs:
                raise ValueError('cannot combine stride with multiple addresses')
            if 'field_stride' in kwargs:
                raise ValueError('cannot combine field-stride with multiple addresses')

        elif isinstance(address, (str, int)):
            base = BitRange.from_spec(regfile.bus_width, address)
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
            if stride < 2**base.size:
                raise ValueError('stride is smaller than the block size')
            if stride & (2**base.size-1):
                raise ValueError('stride is not aligned to the block size')
            field_stride = int(kwargs.pop('field_stride', 2**base.width))
            if field_stride < base.width:
                raise ValueError('field-stride is smaller than the width of a single field')

            self._field_repeat = field_repeat
            self._stride = stride
            self._field_stride = field_stride
            self._bitranges = [base.move(
                (index // field_repeat) * stride,
                (index % field_repeat) * field_stride)
                               for index in range(repeat)]

        else:
            raise ValueError('invalid or missing address')

        # Parse metadata.
        self._meta = Metadata.from_dict(kwargs)
        if any(('register-' + key in kwargs for key in ('mnemonic', 'name', 'brief', 'doc'))):
            self._reg_meta = Metadata.from_dict(kwargs, 'register')
        else:
            self._reg_meta = None

        # Parse type information.
        typ = kwargs.pop('type', 'control')
        # TODO: look up the type code
        self._logic = None

        # Check for unknown keys.
        for key in kwargs:
            raise ValueError('unexpected key in field description: %s' % key)

    @classmethod
    def from_dict(cls, regfile, dictionary):
        """Constructs a field descriptor object from a dictionary."""
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
        if self._field_repeat is None:
            dictionary['address'] = [address.to_spect() for address in self._bitranges]
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
            self._reg_meta.to_dict(dictionary, 'register')

        # Write type information.
        # TODO
        #self._logic.to_dict(dictionary)

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
    def logic(self):
        """Object logic description."""
        return self._logic

    @property
    def regfile(self):
        """Register file that this field is bound to."""
        return self._regfile

    def __getitem__(self, index):
        return Field(
            self._meta[index],
            self._bitranges[index],
            self._logic,
            self,
            index)

    def __len__(self):
        return len(self._bitranges)

    def __iter__(self):
        for index in range(len(self._bitranges)):
            yield self[index]
