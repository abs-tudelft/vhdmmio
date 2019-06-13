"""Module for `Interrupt` objects."""

from .metadata import Metadata

class Interrupt:
    """Class representing the description of an interrupt or vector of
    interrupts."""

    def __init__(self, regfile, **kwargs):
        """Constructs an interrupt from its YAML dictionary representation."""
        self._regfile = regfile
        self._mask_field = None
        self._enable_field = None
        self._index = None

        # Parse metadata first, so we can print error messages properly.
        self._meta = Metadata.from_dict(1, kwargs.copy())
        try:

            # Parse vector width.
            self._width = kwargs.pop('width', None)
            if self._width is not None:
                self._width = int(self._width)

            # Parse metadata again, now with the correct vector width.
            self._meta = Metadata.from_dict(self._width, kwargs)

            # Check for unknown keys.
            for key in kwargs:
                raise ValueError('unexpected key in interrupt description: %s' % key)

        except (ValueError, TypeError) as exc:
            raise type(exc)('while parsing interrupt %s: %s' % (self._meta.name, exc))

    @classmethod
    def from_dict(cls, regfile, dictionary):
        """Constructs a interrupt descriptor object from a dictionary."""
        dictionary = dictionary.copy()
        for key in list(dictionary.keys()):
            if '-' in key:
                dictionary[key.replace('-', '_')] = dictionary.pop(key)
        return cls(regfile, **dictionary)

    def to_dict(self, dictionary=None):
        """Returns a dictionary representation of this object."""
        if dictionary is None:
            dictionary = {}

        # Write vector width.
        if self._width is not None:
            dictionary['width'] = self._width

        # Write metadata.
        self._meta.to_dict(dictionary)

        return dictionary

    @property
    def regfile(self):
        """Points to the parent register file."""
        return self._regfile

    @property
    def meta(self):
        """Metadata for this group of fields."""
        return self._meta

    @property
    def width(self):
        """Vector size of this interrupt, or `None` if the interrupt is
        scalar."""
        return self._width

    @property
    def index(self):
        """Index of this interrupt's LSB in the internal IRQ vector."""
        assert self._index is not None
        return self._index

    @index.setter
    def index(self, value):
        assert self._index is None
        self._index = value

    @property
    def low(self):
        """Index of this interrupt's LSB in the internal IRQ vector."""
        assert self._index is not None
        return self._index

    @property
    def high(self):
        """Index of this interrupt's MSB in the internal IRQ vector."""
        assert self._index is not None
        return self._index + self._width - 1

    @property
    def mask_field(self):
        """Field that controls this interrupt's masking bit(s), or `None` if
        there is no such field."""
        return self._mask_field

    @mask_field.setter
    def mask_field(self, value):
        if self._mask_field is not None:
            raise ValueError('multiple mask fields for interrupt %s' % self.meta.name)
        self._mask_field = value

    @property
    def enable_field(self):
        """Field that controls this interrupt's enable bit(s), or `None` if
        there is no such field."""
        return self._enable_field

    @enable_field.setter
    def enable_field(self, value):
        if self._enable_field is not None:
            raise ValueError('multiple enable fields for interrupt %s' % self.meta.name)
        self._enable_field = value
