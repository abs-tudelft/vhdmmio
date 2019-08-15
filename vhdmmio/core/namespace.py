"""Submodule for the `Namespace` class, which tracks `Named` objects to detect
conflicts."""

class Namespace:
    """Managed set of uniquely named `Named` and nested `Namespace` objects.
    This is used to check uniqueness of the `name` and `mnemonic` values."""

    def __init__(self, name, check_mnemonics=True):
        super().__init__()
        self._check_mnemonics = check_mnemonics
        self._name = name
        self._used_names = {}
        self._used_mnemonics = {} if check_mnemonics else None
        self._ancestors = {}

    @property
    def name(self):
        """Name of the namespace, used for error messages."""
        return self._name

    def __str__(self):
        return self.name

    def _add_mnemonic(self, mnemonic, obj):
        """Registers a new mnemonic."""
        if not self._check_mnemonics:
            return
        if mnemonic in self._used_mnemonics:
            if self._used_mnemonics[mnemonic] != obj:
                raise ValueError('mnemonic %s is used more than once in the '
                                 '%s namespace' % (mnemonic, self))
        self._used_mnemonics[mnemonic] = obj

    def _add_name(self, name, obj):
        """Registers a new name."""
        name = name.lower()
        if name in self._used_names:
            if self._used_names[name] != obj:
                raise ValueError('name %s is used more than once in the '
                                 '%s namespace' % (name, self))
        self._used_names[name] = obj

    def add(self, *named):
        """Adds a `Named` object to the namespace. The object must have a sane
        equality check as well (usually provided by `Unique`) to prevent false
        conflict errors when the same object is added multiple times. If
        multiple objects are specified, they are treated as a hierarchical
        path."""

        # Chains of mnemonics should be unique with _ separator.
        self._add_mnemonic('_'.join(n.mnemonic for n in named), named[-1])

        root, *descendants = named

        # Mnemonics must themselves be unique within a namespace.
        self._add_mnemonic(root.mnemonic, root)

        # So do names.
        self._add_name(root.name, root)

        if not descendants:
            return

        child, *descendants = descendants

        # Names of children must also be unique within their parent's
        # namespace.
        self._add_name(child.name, child)

        # Handle these rules recursively.
        ident = root.name.lower()
        if ident not in self._ancestors:
            self._ancestors[ident] = Namespace('%s::%s' % (self.name, root.name))
        self._ancestors[ident].add(child, *descendants)
