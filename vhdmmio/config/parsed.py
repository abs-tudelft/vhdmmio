"""Submodule for the `Parsed` `Loader`, which allows scalar configuration
values (string, integer, boolean, and technically float) to be parsed and
internally stored with a more convenient representation through a custom
serializer and deserializer function."""

from .loader import ScalarLoader
from .utils import ParseError, Unset

class Parsed(ScalarLoader):
    """Loader for keys with parsed values. Parsed values are deserialized and
    serialized with custom functions. These functions can be set in the
    initializer, using the setter functions, or using the annotation syntax
    (similar to `property`)."""

    def __init__(self, key, doc, default=Unset, deserializer=None, serializer=None):
        super().__init__(key, doc, default)
        self._deserializer = deserializer
        self._serializer = serializer

    def deserializer(self, deserializer):
        """Sets the deserializer function. This function takes the value as the
        first and only positional arguments, and takes the positional arguments
        passed to `__init__` of the parent class as keyword arguments. It must
        return the internal representation of the value.
        """
        self._deserializer = deserializer
        return self

    def serializer(self, serializer):
        """Sets the serializer function. This function must take the value
        returned by the deserializer and turn it back into the configuration
        file representation."""
        self._serializer = serializer
        return self

    def deserialize(self, dictionary, parent):
        """`Parsed` deserializer. See `Loader.deserialize()` for more info."""
        value = self.get_value(dictionary)
        if self._deserializer is None:
            return value
        with ParseError.wrap(self.key):
            return self._deserializer(parent, value)

    def scalar_serialize(self, value):
        """`Parsed` serializer. See `ScalarLoader.scalar_serialize()` for more
        info."""
        if self._serializer is None:
            return value
        return self._serializer(value)

    @classmethod
    def decorator(cls, *args, **kwargs):
        """Returns a decorator for this `Parsed`. It should be applied to a
        function or method, which is used as the deserializer. The serializer
        can be set later with `@<name>.serializer`, similar to
        `property.setter`. The name of the method is the name of the key, and
        its docstring is used as the key's documentation."""
        def fun(method):
            return cls(method.__name__, method.__doc__, *args, deserializer=method, **kwargs)
        return fun


def parsed(method):
    """Method decorator for constructing `Parsed` loaders inside a
    `configurable`-annotated class. The annotated method is the deserialization
    function used for the `Parsed`. It should not take a `self` argument in
    addition. The serialization function can be set with `@<name>.serializer`;
    this method must also not take a `self` argument. The name of the key is
    set to the name of the method, and the markdown documentation for the key
    is set to the method's docstring."""
    return Parsed(method.__name__, method.__doc__, deserializer=method)
