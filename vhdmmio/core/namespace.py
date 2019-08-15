"""Submodule for the `Namespace` class, which tracks `Named` objects to detect
conflicts."""

class Namespace:
    """Managed set of uniquely named `Named` and nested `Namespace` objects.
    This is used to check uniqueness of the `name` and `mnemonic` values."""

    def __init__(self, name):
        super().__init__(self)
        self._name = name
        self._used_names = set()
        self._used_mnemonics = set()
        self._ancestors = {}

    @property
    def name(self):
        """Name of the namespace, used for error messages."""
        return self._name

    def __str__(self):
        return self.name

    def _add_mnemonic(self, mnemonic):
        """Registers a new mnemonic."""
        if mnemonic in self._used_mnemonics:
            raise ValueError('mnemonic %s is used more than once in '
                             'namespace %s' % (mnemonic, self))
        self._used_mnemonics.add(mnemonic)

    def _add_name(self, name):
        """Registers a new name."""
        name = name.lower()
        if name in self._used_names:
            raise ValueError('name %s is used more than once in '
                             'namespace %s' % (name, self))
        self._used_names.add(name)

    def add(self, *named):
        """Adds a `Named` object to the namespace. If multiple objects are
        specified, they are treated as a hierarchical path."""

        # Chains of mnemonics should be unique with _ separator.
        self._add_mnemonic('_'.join(n.mnemonic for n in named))

        root, *descendants = named

        # Mnemonics must themselves be unique within a namespace.
        self._add_mnemonic(root.mnemonic)

        # So do names.
        self._add_name(root.name)

        if not descendants:
            return

        child, *descendants = descendants

        # Names of children must also be unique within their parent's
        # namespace.
        self._add_name(child.name)

        # Handle these rules recursively.
        ident = root.name.lower()
        if ident not in self._ancestors:
            self._ancestors[ident] = Namespace('%s::%s' % (self.name, root.name))
        self._ancestors[ident].add(child, *descendants)
