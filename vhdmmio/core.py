

class Operation(Enum):
    """Enumeration for read vs write."""
    READ = 0
    WRITE = 1


class Metadata:
    """Documentation metadata for register files, registers, and fields."""

    def __init__(self, name, brief='', doc=''):
        """Constructs a new metadata object.

         - `name` must be an identifier.
         - `brief` must either be `None` or a markdown string that serves as a
           one-line description of the register file. Defaults to `name`.
         - `doc` must either be `None` or a markdown string that serves as more
           complete documentation of the register file. Defaults to an empty
           string.
        """
        super().__init__()

        self._name = str(name).strip()
        if not re.match(r'[a-zA-Z][a-zA-Z_0-9]*$', self._name):
            raise ValueError('name {!r} is not a valid identifier'.format(self._name))

        if brief:
            self._brief = str(brief).strip()
            if '\n' in self._brief:
                raise ValueError('brief documentation should not contain newlines')
        else:
            self._brief = self._name

        self._doc = str(doc).strip()

    @classmethod
    def from_dict(cls, dictionary):
        """Constructs a metadata object from the given dictionary, removing the
        keys that were used."""
        return cls(
            dictionary.pop('name'),
            dictionary.pop('brief', ''),
            dictionary.pop('doc', ''))

    def to_dict(self, dictionary):
        """Inverse of `from_dict()`."""
        dictionary['name'] = self.name
        dictionary['brief'] = self.brief
        dictionary['doc'] = self.doc
        return dictionary

    @property
    def name(self):
        """Object name."""
        return self._name

    @property
    def brief(self):
        """Brief description of the object (a single paragraph of markdown)."""
        return self._brief

    @property
    def doc(self):
        """Long description of the object (multiple paragraphs of markdown)."""
        return self._doc


class RegisterFile:
    """Represents a register file description."""

    def __init__(self, meta):
        """Constructs a new register file.

        `meta` must be set to a descriptive `Metadata` object."""
        super().__init__()

        if not isinstance(meta, Metadata):
            raise TypeError('expected Metadata object but found {}'.format(type(meta)))
        self._meta = meta

        self._fields = []

    @classmethod
    def from_dict(cls, dictionary):
        """Constructs a register file from the given dictionary, removing the
        keys that were used."""
        regfile = cls(Metadata(dictionary))
        for field in dictionary.pop('fields'):
            regfile.add_field(Field.from_dict(field, regfile))
            for key in field:
                raise KeyError('unexpected key within field dict: {}'.format(key))
        # interrupts!
        return regfile

    def to_dict(self, dictionary):
        """Inverse of `from_dict()`."""
        self.meta.to_dict(dictionary)
        dictionary['fields'] = [field.to_dict({}) for field in fields]
        return dictionary

    def add_field(self, field):
        """Adds a field to the register file."""
        if not isinstance(field, Field):
            raise TypeError('expected Field object but found {}'.format(type(field)))
        self._fields.append(field)

    def __iter__(self):
        return iter(self._fields)

    def __len__(self):
        return len(self._fields)

    def __getitem__(self, index):
        self._fields[index]

    @property
    def meta(self):
        """Metadata describing this register file."""
        return self._meta


class Field:
    """Representation of a field within a register file."""

    def __init__(self, bitrange, mnemonic, meta, logic, reg_meta=None, regfile=None):
        """Constructs a new field object.

         - `bitrange` must be a `BitRange` object representing the first field
           item. If repetition is performed, this will be auto-incremented.
         - `mnemonic` must be an uppercase string identifying the field. It
           must be unique within the register(s) it exists in, but should
           otherwise be as short as possible. Mnemonics may include digits and
           underscores as well as uppercase letters, but the first and last
           character *must* be an uppercase letter.
         - `meta` must be a `Metadata` object documenting the field.
         - `logic` must be `FieldLogic` object describing the functionality of
           the field.
         - `reg_meta` can optionally specify metadata for the register
           surrounding the field.
         - `regfile` can optionally be used as a backreference to the
           `RegisterFile` object that owns this field.
        """
        super().__init__()

        self._mnemonic = str(name).strip()
        if not re.match(r'[A-Z]([A-Z0-9]*[A-Z])?$', self._mnemonic):
            raise ValueError('name {!r} is not a valid field mnemonic'.format(self._mnemonic))

        self._meta = meta
        if not isinstance(metadata, Metadata):
            raise TypeError('expected Metadata object for meta, received {}'.format(type(metadata)))

        self._logic = logic
        if not isinstance(logic, FieldLogic):
            raise TypeError('expected FieldLogic object for logic, received {}'.format(type(logic)))

        self._reg_meta = reg_meta
        if not isinstance(metadata, Metadata) and reg_meta is not None:
            raise TypeError('expected Metadata object or None for reg_meta, received {}'.format(type(reg_meta)))

        self._regfile = regfile
        if not isinstance(regfile, RegisterFile) and regfile is not None:
            raise TypeError('expected RegisterFile object or None for regfile, received {}'.format(type(regfile)))

    @classmethod
    def from_dict(cls, dictionary, regfile=None):
        """Constructs a field from the given dictionary, removing the keys that
        were used."""
        register = dictionary.pop('register', None)
        if isinstance(register, dict):
            reg_meta = Metadata.from_dict(register)
            for key in register:
                raise KeyError('unexpected key within register dict: {}'.format(key))
        elif register is not None:
            reg_meta = Metadata(register)
        else:
            reg_meta = None

        return cls(
            dictionary.pop('mnemonic'),
            Metadata.from_dict(dictionary),
            FieldLogic.from_dict(dictionary),
            reg_meta,
            regfile)

    def to_dict(self, dictionary):
        """Inverse of `from_dict()`."""
        if self.reg_meta is not None:
            dictionary['register'] = self.reg_meta.to_dict({})
        dictionary['mnemonic'] = self.mnemonic
        self.meta.to_dict(dictionary)
        self.logic.to_dict(dictionary)
        return dictionary

    @property
    def mnemonic(self):
        """Mnemonic for the field."""
        return self._mnemonic

    @property
    def meta(self):
        """Metadata for the field."""
        return self._meta

    @property
    def logic(self):
        """`FieldLogic` object associated with the field."""
        return self._logic

    @property
    def reg_meta(self):
        """Metadata for the surrounding register, or `None` if not defined."""
        return self._reg_meta

    @property
    def regfile(self):
        """Reference to the surrounding register file, or `None` if not defined."""
        return self._regfile


class FieldLogic:
    """Base class for the logic that defines how a field works."""

    def __init__(self, type_name, read_caps, write_caps):
        super().__init__()
        self._type_name = str(type_name)
        self._read_caps = read_caps
        self._write_caps = write_caps

    @classmethod
    def from_dict(cls, dictionary):
        """Constructs a FieldLogic from the given dictionary, removing the keys
        that were used."""
        # TODO: placeholder code (need subclasses based on type name)
        return cls(dictionary.pop('type'), FieldCapabilities(), FieldCapabilities())

    def to_dict(self, dictionary):
        """Inverse of `from_dict()`."""
        # TODO: placeholder code (need subclasses based on type name)
        dictionary['type'] = self._type_name
        return dictionary

    @property
    def read_caps(self):
        """Capability flags for this field for read operations."""
        return self._read_caps

    @property
    def write_caps(self):
        """Capability flags for this field for write operations."""
        return self._write_caps

    def get_caps(self, operation):
        """Returns the capability flags for this field for the given
        `Operation`."""
        if operation == Operation.READ:
            return self.read_caps
        if operation == Operation.WRITE:
            return self.write_caps
        raise TypeError('expected Operation, received {}'.format(type(operation)))


class FieldCapabilities:
    """Class maintaining flags indicating the capabilities of a field for
    either a specific operation (read or write)."""

    def __init__(self,
        volatile=False, can_block=False, can_defer=False,
        allow_user=True, allow_nonsecure=True, allow_instruction=False):
        super().__init__()
        self._volatile = volatile
        self._can_block = can_block
        self._can_defer = can_defer
        self._allow_user = allow_user
        self._allow_nonsecure = allow_nonsecure
        self._allow_instruction = allow_instruction

    @property
    def volatile(self):
        """Returns whether there is a functional difference between performing
        the same exact operation on this field once or twice. Volatile fields
        cannot be combined with blocking fields within the same register."""
        return self._volatile

    @property
    def can_block(self):
        """Returns whether accessing this field can cause the bus to stall.
        Blocking fields cannot be combined with other blocking fields or
        volatile fields within the same register."""
        return self._can_block

    @property
    def can_defer(self):
        """Returns whether accesses to this field can be deferred = whether
        multiple outstanding requests are supported = whether the request
        pipeline can advance before the response is returned. Fields that have
        this flag set must be the only field within a register."""
        return self._can_defer

    @property
    def allow_user(self):
        """Whether user-mode/unpriviliged accesses (AxPROT bit 0 set) are
        allowed. All fields within a register must have this set to the same
        value."""
        return self._allow_user

    @property
    def allow_nonsecure(self):
        """Whether accesses marked non-secure (AxPROT bit 1 set) are
        allowed. All fields within a register must have this set to the same
        value."""
        return self._allow_nonsecure

    @property
    def allow_instruction(self):
        """Whether instruction accesses (AxPROT bit 2 set) are allowed. All
        fields within a register must have this set to the same value."""
        return self._allow_instruction


