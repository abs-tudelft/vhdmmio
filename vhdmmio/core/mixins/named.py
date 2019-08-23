"""Submodule for named/user-documented objects."""

import re
from ...configurable import Unset
from ...config import MetadataConfig
from ...utils import doc_enumerate

class ContextualError(Exception):
    """Used for reraising exceptions with the name and type of the `Named`
    class causing the exception included as contextual information."""

    def __init__(self, msg, *contexts):
        super().__init__(msg)
        self._context = []
        for context in contexts:
            self.add_context(context)

    def add_context(self, context):
        """Adds context to this error message."""
        context = str(context)
        if context not in self._context:
            self._context.insert(0, context)

    def __str__(self):
        msg = super().__str__()
        if not self._context:
            return msg
        return 'error within %s: %s' % (doc_enumerate(self._context), msg)

    @staticmethod
    def handle(exc_typ, exc_val, context):
        """Add context to the given exception, raising a new
        `ContextualError` if necessary."""
        if exc_typ is ContextualError:
            exc_val.add_context(context)
            return
        message = str(exc_val)
        if exc_typ is not ValueError:
            message = '%s (%s)' % (message, exc_typ.__name__)
        raise ContextualError(message, context)


class Named:
    """Base class for register file components that have a mnemonic, name, and
    documentation attached to them."""

    def __init__(self, metadata=None, name=None,
                 mnemonic_suffix='', name_suffix='',
                 doc_index='', brief_override=None, doc_override=None,
                 **kwargs):
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

        # Now that we have a name, context will work.
        with self.context:

            # Determine brief.
            if brief_override is not None:
                self._brief = brief_override
            elif metadata.brief is Unset:
                self._brief = self._name + '.'
            else:
                self._brief = metadata.brief.replace('{index}', doc_index)

            # Determine doc.
            if doc_override is not None:
                self._doc = doc_override
            elif metadata.doc is Unset:
                self._doc = None
            else:
                self._doc = metadata.doc.replace('{index}', doc_index)

            # Chain to next class in the MRO.
            super().__init__(**kwargs)

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
        """Extended documentation of this object, to be read in addition to
        `brief`. Multiple lines of markdown-formatted text."""
        return self._doc

    @property
    def extended_doc(self):
        """Complete documentation for this object, including brief. Multiple
        lines of markdown-formatted text."""
        extended_doc = self.brief[:1].upper() + self.brief[1:]
        if self.doc is not None:
            extended_doc += '\n\n' + extended_doc
        return extended_doc

    @property
    def context(self):
        """Adds contextual information to any exceptions thrown within a
        `with` block applied to this value."""
        class Context:
            """Context manager class that reraises exceptions thrown within the
            context as `ContextualError`s carrying information about the parent
            `Named` class."""
            @staticmethod
            def __enter__():
                pass
            @staticmethod
            def __exit__(exc_typ, exc_val, _):
                if exc_val is None:
                    return
                ContextualError.handle(exc_typ, exc_val, self)
        return Context()

    def context_if(self, condition):
        """Returns a context manager that adds contextual information to any
        exceptions thrown, if the given condition is true. Otherwise a no-op
        context manager is returned."""
        if condition:
            return self.context
        class DummyContext:
            """Dummy context manager."""
            @staticmethod
            def __enter__():
                pass
            @staticmethod
            def __exit__(*_):
                pass
        return DummyContext()

    def get_type_name(self):
        """Returns a friendly representation of this object's type, used for
        context in user-facing error messages. By default, this just converts
        TitleCase to lowercase words. If this isn't good enough, the method can
        be overridden."""
        return ' '.join(re.findall(r'\w[a-z0-9_]+', type(self).__name__)).lower()

    def __str__(self):
        return '%s "%s"' % (self.get_type_name(), self.name)

    def __repr__(self):
        return '%s(name=%r)' % (type(self).__name__, self.name)
