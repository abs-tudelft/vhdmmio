"""Submodule for the `Unique` mixin."""

class Unique:
    """Mixins for unique objects, for which regular equality equals object ID
    equality. This allows the objects to be hashable."""

    def __hash__(self):
        return id(self)

    def __eq__(self, other):
        return self is other

    def __ne__(self, other):
        return self is not other
