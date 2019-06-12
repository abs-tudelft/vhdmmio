"""Module for `RegisterFile` object."""

from .metadata import Metadata, ExpandedMetadata
from .field import FieldDescriptor
from .register import Register

class RegisterFile:
    """Represents a register file."""

    def __init__(self, **kwargs):
        """Constructs a register file from its YAML description."""

        # Parse metadata.
        meta = kwargs.pop('meta', None)
        if meta is None:
            raise ValueError('missing meta key for register file')
        meta = meta.copy()
        self._meta = Metadata.from_dict(None, meta)
        for key in meta:
            raise ValueError('unexpected key in register file metadata: %s' % key)

        try:

            # Parse bus width.
            self._bus_width = int(kwargs.pop('bus_width', 32))
            if self._bus_width not in (32, 64):
                raise ValueError('bus-width must be 32 or 64')

            # Read the fields.
            self._field_descriptors = tuple((
                FieldDescriptor.from_dict(self, d) for d in kwargs.pop('fields', [])))

            # Construct registers from the fields.
            reg_map = {}
            for field_descriptor in self._field_descriptors:
                for field in field_descriptor.fields:
                    addr = field.bitrange.address
                    if addr not in reg_map:
                        reg_map[addr] = []
                    reg_map[addr].append(field)
            self._registers = tuple((Register(*fields) for _, fields in sorted(reg_map.items())))

            # Check for overlapping registers. Note that this assumes that the
            # registers are ordered by address, which we do in the one-liner above.
            min_read = 0
            prev_read = None
            min_write = 0
            prev_write = None
            for register in self._registers:
                if register.read_caps is not None:
                    if register.address < min_read:
                        raise ValueError('registers %s and %s overlap in read mode'
                                         % (prev_read, register))
                    min_read = register.address_high + 1
                    prev_read = register
                if register.write_caps is not None:
                    if register.address < min_write:
                        raise ValueError('registers %s and %s overlap in write mode'
                                         % (prev_write, register))
                    min_write = register.address_high + 1
                    prev_write = register

            # Check for naming conflicts.
            ExpandedMetadata.check_siblings((
                reg.meta
                for reg in self._registers))
            ExpandedMetadata.check_cousins((
                field.meta
                for reg in self._registers
                for field in reg.fields))

            # Check for unknown keys.
            for key in kwargs:
                raise ValueError('unexpected key in field description: %s' % key)

        except (ValueError, TypeError) as exc:
            raise type(exc)('while parsing register file %s: %s' % (self._meta.name, exc))

    @classmethod
    def from_dict(cls, dictionary):
        """Constructs a register file object from a dictionary."""
        dictionary = dictionary.copy()
        for key in list(dictionary.keys()):
            if '-' in key:
                dictionary[key.replace('-', '_')] = dictionary.pop(key)
        return cls(**dictionary)

    def to_dict(self, dictionary=None):
        """Returns a dictionary representation of this register file."""
        if dictionary is None:
            dictionary = {}

        # Write metadata.
        dictionary['meta'] = {}
        self._meta.to_dict(dictionary['meta'])

        # Write fields.
        dictionary['fields'] = []
        for field in self._field_descriptors:
            dictionary['fields'].append(field.to_dict())

        return dictionary

    @property
    def meta(self):
        """Metadata for this register file."""
        return self._meta[None]

    @property
    def bus_width(self):
        """Returns the bus width for this register file."""
        return self._bus_width

    @property
    def field_descriptors(self):
        """Returns the collection of field descriptors that are part of this
        register file."""
        return self._field_descriptors

    @property
    def registers(self):
        """Returns the collection of registers that are part of this register
        file."""
        return self._registers

    def __str__(self):
        return self.meta.name
