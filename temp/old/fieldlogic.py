"""Module for the `FieldLogic` base class."""

from .accesscaps import ReadWriteCapabilities

class logic:
    """Decorator for child classes of `FieldLogic` that ensures that they're
    registered correctly."""
    #pylint: disable=C0103,W0212,R0903
    def __init__(self, typ):
        super().__init__()
        assert isinstance(typ, str)
        self._typ = typ

    def __call__(self, cls):
        assert issubclass(cls, FieldLogic)
        assert self._typ not in FieldLogic._TYPE_LOOKUP
        FieldLogic._TYPE_LOOKUP[self._typ] = cls
        cls._TYPE_CODE = self._typ
        return cls

class FieldLogic(ReadWriteCapabilities):
    """Base class for representing the hardware description of this register
    and its interface to the user's logic."""

    _TYPE_CODE = None
    _TYPE_LOOKUP = {}

    @staticmethod
    def from_dict(dictionary):
        """Constructs a `FieldLogic` object from a dictionary. The key `'type'`
        is used to select the subclass to use."""
        typ = dictionary.pop('type', 'control')
        cls = FieldLogic._TYPE_LOOKUP.get(typ, None)
        if cls is None:
            raise ValueError('unknown type code "%s"' % typ)
        return cls.from_dict(dictionary)

    def to_dict(self, dictionary):
        """Returns a dictionary representation of this object."""
        dictionary['type'] = self.type_code

    @property
    def type_code(self):
        """Returns the type code of this field."""
        return self._TYPE_CODE
