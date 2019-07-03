"""Module for `Metadata` and `ExpandedMetadata` objects."""

import re

class Metadata:
    """Documentation metadata for register files, registers, and fields."""

    def __init__(self, count=None, mnemonic=None, name=None, brief=None, doc=None):
        """Constructs a new metadata object.

         - `count` is the number of times the object represented by this
           metadata object is repeated in array-form, or `None` if it is a
           scalar.
         - `mnemonic`, if specified, must be an uppercase string that can only
           have digits and underscores after the first character. When `count`
           is not `None`, they also cannot end in a digit. Mnemonics must be
           unique among the siblings of the object that this metadata
           represents.
         - `name`, if specified, must be a valid identifier like mnemonic, but
           can also have lowercase letters. Names must be unique among the
           siblings and cousins of the object that this metadata represents.
         - `brief`, if specified, must be a markdown string that serves as a
           one-line description of the register file. Newline characters are
           not allowed at all, even if they would not open a new paragraph in
           markdown.
         - `doc`, if specified, must be a markdown string that serves as more
           complete documentation of the represented objct.

        Either `mnemonic`, `name`, or both must be specified. If one is
        missing, it's derived from the other. `brief` defaults to the outcome
        for `name` (with an attempt to convert it to a sentence), while `doc`
        defaults to an empty string."""
        super().__init__()

        if mnemonic is None and name is None:
            raise ValueError('either name or mnemonic must be specified')

        if count is None:
            self._count = None
        else:
            self._count = int(count)
            if self._count < 1:
                raise ValueError('count must be positive')

        # Parse and check mnemonic.
        if mnemonic is None:
            self._mnemonic = str(name).upper()
        else:
            self._mnemonic = str(mnemonic)
        if not re.match(r'[A-Z][A-Z_0-9]*$', self._mnemonic):
            raise ValueError('name {!r} is not a valid mnemonic'.format(self._mnemonic))
        if count is not None and re.search(r'[0-9]$', self._mnemonic):
            raise ValueError('mnemonic cannot end in a digit when repetition is used')

        # Parse and check name.
        if name is None:
            self._name = str(mnemonic).lower()
        else:
            self._name = str(name)
        if not re.match(r'[a-zA-Z][a-zA-Z_0-9]*$', self._name):
            raise ValueError('name {!r} is not a valid identifier'.format(self._name))
        if count is not None and re.search(r'[0-9]$', self._name):
            raise ValueError('name cannot end in a digit when repetition is used')

        # Parse and check brief.
        if brief is None:
            brief = re.split(r'([0-9]+)|([A-Z]*)(?:_|([0-9]+|[A-Z][a-z]+))', self._name)
            brief = ' '.join(filter(bool, brief))
            self._brief = brief[0].upper() + brief[1:] + '.'
        else:
            self._brief = str(brief)
        if '\n' in self._brief:
            raise ValueError('brief documentation contains one or more newlines')

        # Parse and check doc.
        if doc is None:
            self._doc = ''
        else:
            self._doc = str(doc)

    @classmethod
    def from_dict(cls, count, dictionary, prefix=''):
        """Constructs a metadata object from the given dictionary, removing the
        keys that were used."""
        return cls(
            count,
            dictionary.pop(prefix + 'mnemonic', None),
            dictionary.pop(prefix + 'name', None),
            dictionary.pop(prefix + 'brief', None),
            dictionary.pop(prefix + 'doc', None))

    def to_dict(self, dictionary, prefix=''):
        """Inverse of `from_dict()`."""
        dictionary[prefix + 'mnemonic'] = self.mnemonic
        dictionary[prefix + 'name'] = self.name
        dictionary[prefix + 'brief'] = self.markdown_brief
        dictionary[prefix + 'doc'] = self.markdown_doc
        return dictionary

    @property
    def mnemonic(self):
        """Object mnemonic."""
        return self._mnemonic

    @property
    def name(self):
        """Object name."""
        return self._name

    @property
    def markdown_brief(self):
        """Brief description of the object (a single line of markdown)."""
        return self._brief

    @property
    def markdown_doc(self):
        """Long description of the object (multiple lines/paragraphs of
        markdown)."""
        return self._doc

    @property
    def count(self):
        """Size of the array that this metadata object describes, or `None` if
        it does not describe an array."""
        return self._count

    def __len__(self):
        """Number of repetitions."""
        return self._count

    def __getitem__(self, index=None):
        """"Expands" this `Metadata` object into an `ExpandedMetadata` using
        the specified object index, or the full range if no index is
        specified."""
        return ExpandedMetadata(self, index)

    def __iter__(self):
        for i in range(self._count):
            yield self[i]

class ExpandedMetadata:
    """Same as `Metadata`, but expanded for a specific index within a repeated
    object."""

    def __init__(self, metadata, index=None):
        """"Expands" a `Metadata` object into an `ExpandedMetadata` using the
        specified object index, or the full range if no index is specified."""
        if index is not None:
            if metadata.count is None or (index < 0 or index >= metadata.count):
                raise ValueError('index out of range')

        if metadata.count is None:
            self._singular = True
            self._mnemonic = metadata.mnemonic
            self._name = metadata.name
            self._md_mnemonic = '`' + metadata.mnemonic + '`'
            self._md_name = '`' + metadata.name + '`'
            self._brief = metadata.markdown_brief.replace('{index}', '')
            self._doc = metadata.markdown_doc.replace('{index}', '')
        elif index is None:
            ident = '*0..%d*' % (metadata.count - 1)
            self._singular = False
            self._mnemonic = None
            self._name = None
            self._md_mnemonic = '`' + metadata.mnemonic + '`' + ident
            self._md_name = '`' + metadata.name + '`' + ident
            self._brief = metadata.markdown_brief.replace('{index}', ident)
            self._doc = metadata.markdown_doc.replace('{index}', ident)
        else:
            ident = '%d' % index
            self._singular = True
            self._mnemonic = metadata.mnemonic + ident
            self._name = metadata.name + ident
            self._md_mnemonic = '`' + metadata.mnemonic + ident + '`'
            self._md_name = '`' + metadata.name + ident + '`'
            self._brief = metadata.markdown_brief.replace('{index}', ident)
            self._doc = metadata.markdown_doc.replace('{index}', ident)

    @property
    def singular(self):
        """Returns whether this is metadata for a singular object vs a range of
        similar objects."""
        return self._singular

    @property
    def mnemonic(self):
        """Object mnemonic for use within code output."""
        if not self.singular:
            raise ValueError('cannot get mnemonic for range of objects')
        return self._mnemonic

    @property
    def name(self):
        """Object name for use within code output."""
        if not self.singular:
            raise ValueError('cannot get name for range of objects')
        return self._name

    @property
    def markdown_mnemonic(self):
        """Object mnemonic for use within documentation output."""
        return self._md_mnemonic

    @property
    def markdown_name(self):
        """Object name for use within documentation output."""
        return self._md_name

    @property
    def markdown_brief(self):
        """Brief description of the object for use within documentation
        output."""
        return self._brief

    @property
    def markdown_doc(self):
        """Long description of the object for use within documentation
        output."""
        return self._doc

    def to_markdown(self, header=1):
        """Generates basic markdown from this metadata object with the
        specified header level."""
        return '%s %s (%s)\n\n%s\n\n%s\n\n' % (
            '#' * header,
            self.markdown_name,
            self.markdown_mnemonic,
            self.markdown_brief,
            self.markdown_doc)

    @staticmethod
    def check_siblings(siblings):
        """Checks for mnemonic conflicts between siblings."""
        mnemonics = {}
        for sibling in siblings:
            conflict = mnemonics.get(sibling.mnemonic, None)
            if conflict is not None:
                raise ValueError(
                    'mnemonics for %s and %s are both %s' %
                    (sibling.name, conflict.name, sibling.mnemonic))
            mnemonics[sibling.mnemonic] = sibling

    @staticmethod
    def check_cousins(cousins):
        """Checks for name conflicts between cousins."""
        names = {}
        for cousin in cousins:
            conflict = names.get(cousin.name.lower(), None)
            if conflict is not None:
                raise ValueError(
                    'duplicate name %s' % cousin.name)
            names[cousin.name.lower()] = cousin
