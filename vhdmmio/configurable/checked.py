"""Submodule for the `Checked` `Loader`, which allows a custom validation
function to be used to check and deserialize values. The internal
representation of the configuration value is simply its canonical form."""

from .loader import ScalarLoader
from .utils import ParseError

class Checked(ScalarLoader):
    """Loader for keys with checked values. This kind of value does not have
    any meaningful serialization: the internal representation is identical to
    the (canonical) serialized representation. However, deserialization goes
    through a custom validation function, which returns the canonical form."""

    def __init__(self, key, doc, validator, has_default=False):
        super().__init__(key, doc)
        self._validator = validator
        self._has_default = has_default

    def has_default(self):
        """Override `has_default()` based on how the loader was constructed,
        while keeping the default value set to `Unset`."""
        return self._has_default

    def deserialize(self, dictionary, parent):
        """`Checked` deserializer. See `Loader.deserialize()` for more info."""
        value = self.get_value(dictionary)
        with ParseError.wrap(self.key):
            return self._validator(parent, value)


def checked(method):
    """Method decorator for constructing `Checked` loaders inside a
    `configurable`-annotated class. The annotated method is the validator
    function. It is called with the parent and the value (so it essentially
    takes a `self` argument) and must return a canonical version of value
    (which may just be value). The name of the key is set to the name of the
    method, and the markdown documentation for the key is set to the method's
    docstring."""
    return Checked(method.__name__, method.__doc__, method)

def opt_checked(method):
    """Like `@checked`, but it is legal to not specify the value. In this case,
    the special `Unset` value is passed to the validation function. Storing
    `Unset` causes the key to not be emitted during serialization."""
    return Checked(method.__name__, method.__doc__, method, True)
