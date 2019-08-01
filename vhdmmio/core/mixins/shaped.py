"""Submodule for handling objects that can either be a scalar or a vector of a
fixed size."""

class Shaped:
    """Class for objects that can either be a scalar or a vector of a fixed
    size."""

    def __init__(self, shape=None, **kwargs):
        super().__init__(**kwargs)
        self._shape = shape

    @property
    def shape(self):
        """The shape of the object, which is `None` for scalars and the number
        of entries for vectors."""
        return self._shape

    @property
    def width(self):
        """The width of the object, which is 1 for scalars and the number of
        entries for vectors."""
        return 1 if self._shape is None else self._shape

    def is_scalar(self):
        """Returns whether this object is scalar."""
        return self._shape is None

    def is_vector(self):
        """Returns whether this object is a vector."""
        return self._shape is not None

    def describe_shape(self):
        """Returns a human-readable string representation of the shape for use
        in error messages."""
        return 'a scalar' if self._shape is None else 'a vector of size %d' % self._shape
