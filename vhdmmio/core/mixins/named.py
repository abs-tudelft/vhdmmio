"""Submodule for namespace management."""

from ...configurable import Unset
from ...config import MetadataConfig

class Named:
    """Base class for register file components that have a mnemonic, name, and
    documentation attached to them."""

    def __init__(self, metadata=None, name=None,
                 mnemonic_suffix='', name_suffix='',
                 doc_index='', brief_override=None, doc_override=None,
                 **kwargs):
        super().__init__(**kwargs)

        assert metadata is not None or name is not None

        # Instead of supplying a complete metadata object, just a name is okay
        # too.
        if metadata is None:
            metadata = MetadataConfig(name=name)

        # Check for context-sensitive configuration errors.
        if metadata.mnemonic is Unset and metadata.name is Unset:
            raise ValueError('missing mnemonic/name; specify at least one')

        # Determine mnemonic.
        mnemonic = metadata.mnemonic
        if mnemonic is Unset:
            mnemonic = metadata.name.upper()
        self._mnemonic = mnemonic + mnemonic_suffix

        # Determine name.
        name = metadata.name
        if name is Unset:
            name = metadata.mnemonic.lower()
        self._name = name + name_suffix

        # Determine brief.
        if brief_override is not None:
            self._brief = brief_override
        elif metadata.brief is Unset:
            self._brief = self._name + '.'
        else:
            self._brief = metadata.brief.replace('{index}', doc_index)

        # Determine doc.
        if doc_override is not None:
            doc = doc_override
        elif metadata.doc is Unset:
            doc = None
        else:
            doc = metadata.doc.replace('{index}', doc_index)
        self._doc = self._brief[:1].upper() + self._brief[1:]
        if doc is not None:
            self._doc += '\n\n' + doc

    @property
    def mnemonic(self):
        """The mnemonic for this object. Valid uppercase identifier, unique
        among siblings."""
        return self._mnemonic

    @property
    def name(self):
        """The name of this object. Valid identifier, unique among siblings and
        cousins."""
        return self._name

    @property
    def brief(self):
        """Brief description of this object. Single line of markdown-formatted
        text."""
        return self._brief

    @property
    def doc(self):
        """Complete documentation for this object, including brief. Multiple
        lines of markdown-formatted text."""
        return self._doc

    def __str__(self):
        return '%s %s' % (type(self).__name__, self.name)

    def __repr__(self):
        return '%s(name=%r)' % (type(self).__name__, self.name)


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
