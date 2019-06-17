"""Module that maintains the registry of types """

import importlib
import os

_TYPE_LOOKUP = {}
_ALL_LOADED = []

class field_logic:
    """Decorator for child classes of `FieldLogic` that ensures that they're
    registered correctly."""
    #pylint: disable=C0103,W0212,R0903

    def __init__(self, typ):
        super().__init__()
        assert isinstance(typ, str)
        self._typ = typ

    def __call__(self, cls):
        assert self._typ not in _TYPE_LOOKUP
        _TYPE_LOOKUP[self._typ] = cls
        cls._TYPE_CODE = self._typ
        return cls

def type_lookup(typ):
    """Returns the `FieldLogic` class that was registered for the given type
    code."""

    # Make sure that all logic_*.py modules are loaded, since they add items
    # to the registry.
    if not _ALL_LOADED:
        for fname in os.listdir(os.path.dirname(__file__)):
            if fname == 'logic_registry.py':
                continue
            if fname.startswith('logic_') and fname.endswith('.py'):
                importlib.import_module('vhdmmio.core.logic_%s' % fname[6:-3])
        _ALL_LOADED.append(True)

    cls = _TYPE_LOOKUP.get(typ, None)
    if cls is None:
        raise ValueError('unknown type code "%s"' % typ)
    return cls
