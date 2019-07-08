"""Module with abstractions for VHDL types."""

from collections import OrderedDict
from .expressions import expr

def _count_and_offset_to_high_and_low(count, offset):
    high = expr(offset) + expr(count) - 1
    low = str(offset)
    return high, low

class _Base():
    """Base class for abstracting VHDL types.

    Before a non-primitive type can be used in VHDL, it must be defined. You
    can fetch the required definitions using `get_defs()` (for one complex
    type) or `gather_defs()` (for multiple complex types).

    Unlike VHDL, these types carry a default value. For complex types, these
    default values are written to VHDL as constants. The idea is that any
    complex signal or variable has a sane default/reset value associated with
    it, versus just the default 'U' and so on."""

    def __init__(self, name, default):
        """Constructs the base class; don't call this directly."""
        self._name = name
        self._default = default

    @property
    def name(self):
        """Returns the name of this type."""
        return self._name

    @property
    def default(self):
        """Returns the default value for this type."""
        return self._default

    @property
    def incomplete(self):
        """Indicates whether this is an incomplete array type."""
        return False

    @property
    def primitive(self):
        """Indicates whether this is a primitive type."""
        return False

    @staticmethod
    def get_range(count, offset=0):
        """Returns the code for a range of this array type of `count`
        elements starting at `offset`. Whether the range is ascending
        or descending depends on the type."""
        high, low = _count_and_offset_to_high_and_low(count, offset)
        return '%s to %s' % (low, high)

    @staticmethod
    def __len__():
        """Returns the number of bits in this type."""
        raise NotImplementedError('base class for VHDL types does not have a bit count')

    def __str__(self):
        """Returns the name of this type, including suffix."""
        if self.primitive:
            return self.name
        return self.name + '_type'

    @staticmethod
    def get_defs():
        """Returns the type definition(s) for this type as a list of strings
        representing lines of code."""
        return []

    def gather_types(self, into=None):
        """Gather all the types needed by this type into an ordered dict from
        name to type."""
        if into is None:
            into = OrderedDict()
        if not self.primitive:
            prev = into.get(str(self), None)
            if prev is None:
                into[str(self)] = self
            elif prev != self:
                raise ValueError('type name conflict: %s' % self)
        return into

    def gather_members(self, _=None):
        """Yields all members of this type as `(path, type, count)`
        three-tuples. `path` is a list of `str`ings and `int`s, where a
        `str`ing means the name of a record member and an int means an array
        index. `type` is a primitive type. `count` is used for the number of
        bits in `std_logic_vector`s. Incomplete array types need an input
        `count` as well for the number of elements in the vector/array."""
        assert self.primitive
        assert not self.incomplete
        yield [], self, None

    def make_object(self, name):
        """Construct an object reference for an instantiation of this type with
        the given name or identifier path."""
        return Object(name, self)

    def _instantiate(self, fmt, name, arg):
        typ = str(self)
        if self.incomplete:
            anonymous_subtype = SizedArray(None, self, arg)
            typ += '(%s)' % self.get_range(anonymous_subtype.count) #pylint: disable=E1101
            default = anonymous_subtype.default
        elif arg is not None:
            default = arg
        else:
            default = self.default
        return fmt.format(name=name, default=str(default), typ=typ), self.make_object(name)

    def make_input(self, name, arg=None):
        """Makes an input signal from this type. Returns a two-tuple of the
        signal declaration string excluding semicolon and the instantiated
        object."""
        return self._instantiate('{name} : in {typ}@:= {default}', name, arg)

    def make_output(self, name, arg=None):
        """Makes an output signal from this type. Returns a two-tuple of the
        signal declaration string excluding semicolon and the instantiated
        object."""
        return self._instantiate('{name} : out {typ}@:= {default}', name, arg)

    def make_signal(self, name, arg=None):
        """Makes an internal signal from this type. Returns a two-tuple of the
        signal declaration string excluding semicolon and the instantiated
        object."""
        return self._instantiate('signal {name} : {typ}@:= {default}', name, arg)

    def make_variable(self, name, arg=None):
        """Makes a variable from this type. Returns a two-tuple of the
        signal declaration string excluding semicolon and the instantiated
        object."""
        return self._instantiate('variable {name} : {typ}@:= {default}', name, arg)

    def make_constant(self, name, arg=None):
        """Makes a constant from this type. Returns a two-tuple of the
        signal declaration string excluding semicolon and the instantiated
        object."""
        return self._instantiate('constant {name} : {typ}@:= {default}', name.upper(), arg)

    def make_generic(self, name, arg=None):
        """Makes a generic from this type. Returns a two-tuple of the
        signal declaration string excluding semicolon and the instantiated
        object."""
        return self._instantiate('{name} : {typ}@:= {default}', name.upper(), arg)

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        if type(self) != type(other): #pylint: disable=C0123
            return False
        if self.name != other.name:
            return False
        return True


class StdLogic(_Base):
    """Representation of the `std_logic` primitive."""

    def __init__(self, default=0):
        """Constructs an `std_logic` representation with the given default
        value."""
        super().__init__('std_logic', "'%s'" % default)

    @staticmethod
    def __len__():
        """Returns the number of bits in this type."""
        return 1

    @staticmethod
    def get_range(count, offset=0):
        """Returns the code for a range of this array type of `count`
        elements starting at `offset`. Whether the range is ascending
        or descending depends on the type."""
        high, low = _count_and_offset_to_high_and_low(count, offset)
        return '%s downto %s' % (high, low)

    @property
    def primitive(self):
        """Indicates whether this is a primitive type."""
        return True


class Natural(_Base):
    """Representation of the `std_logic` primitive."""

    def __init__(self, default=0):
        """Constructs an `std_logic` representation with the given default
        value."""
        super().__init__('natural', str(default))

    @staticmethod
    def __len__():
        """Returns the number of bits in this type."""
        raise ValueError('naturals cannot be represented as bits')

    @property
    def primitive(self):
        """Indicates whether this is a primitive type."""
        return True


class Boolean(_Base):
    """Representation of the `std_logic` primitive."""

    def __init__(self, default=False):
        """Constructs an `std_logic` representation with the given default
        value."""
        if default is False:
            default = 'false'
        elif default is True:
            default = 'true'
        super().__init__('boolean', str(default))

    @staticmethod
    def __len__():
        """Returns the number of bits in this type."""
        raise ValueError('booleans cannot be represented as bits')

    @property
    def primitive(self):
        """Indicates whether this is a primitive type."""
        return True


class Axi4Lite(_Base):
    """Representations of the `axi4l##_#s#_type` records defined in
    `vhdmmio_pkg`."""

    def __init__(self, component, width=32):
        """Constructs an AXI bus type."""
        component_map = {
            'm2s':  'axi4l{width}_m2s',
            's2m':  'axi4l{width}_s2m',
            'req':  'axi4l{width}_m2s',
            'resp': 'axi4l{width}_s2m',
            'aw':   'axi4la',
            'w':    'axi4lw{width}',
            'b':    'axi4lb',
            'ar':   'axi4la',
            'r':    'axi4lr{width}',
            'h':    'axi4lh',
            'a':    'axi4la',
            'u':    'axi4lu',
        }
        base = component_map.get(component, None)
        if base is None:
            raise ValueError('unknown component %s' % component)
        if width not in [32, 64]:
            raise ValueError('width must be 32 or 64')
        base = base.format(width=width)
        super().__init__(base, base.upper() + '_RESET')

    @staticmethod
    def __len__():
        """Returns the number of bits in this type."""
        raise ValueError('AXI records cannot be represented as bits')

    @property
    def primitive(self):
        """Indicates whether this is a primitive type."""
        return True

    def __str__(self):
        """Returns the name of this type, including suffix."""
        return self.name + '_type'


class Array(_Base):
    """Representation of an incomplete array type."""

    def __init__(self, name, element_type, auto_generated=False):
        """Constructs an incomplete array type from the given element type."""
        super().__init__(name, '(others => %s)' % element_type.default)
        self._auto_generated = auto_generated
        self._element_type = element_type

    @property
    def incomplete(self):
        """Indicates whether this is an incomplete array type."""
        return True

    @property
    def element_type(self):
        """Returns the underlying element type."""
        return self._element_type

    @property
    def primitive(self):
        """Indicates whether this is a primitive type."""
        return self._auto_generated and self._element_type.primitive

    def __len__(self):
        """Returns the number of bits in this type."""
        raise ValueError('incomplete array does not have a bit count yet')

    def __str__(self):
        """Returns the name of this type, including suffix."""
        return self.name + '_array'

    def get_defs(self):
        """Returns the type definition(s) for this type as a list of strings
        representing lines of code."""
        return ['type %s is array (natural range <>) of %s;' % (
            self, self.element_type)]

    def gather_types(self, into=None):
        """Gather all the types needed by this type into an ordered dict from
        name to type."""
        into = self.element_type.gather_types(into)
        return super().gather_types(into)

    def gather_members(self, count=None):
        """Yields all members of this type as `(path, type, count)`
        three-tuples. `path` is a list of `str`ings and `int`s, where a
        `str`ing means the name of a record member and an int means an array
        index. `type` is a primitive type. `count` is used for the number of
        bits in `std_logic_vector`s. Incomplete array types need an input
        `count` as well for the number of elements in the vector/array."""
        if count is None:
            raise ValueError('count must not be None for an incomplete array')
        for i in range(count):
            for subpath, subtype, subcount in self.element_type.gather_members():
                yield [i] + subpath, subtype, subcount

    def __eq__(self, other):
        if not super().__eq__(other):
            return False
        if self.element_type != other.element_type:
            return False
        return True


class StdLogicVector(Array):
    """Representation of the `std_logic_vector` primitive."""

    def __init__(self, bit_default=0):
        """Constructs an `std_logic` representation with the given default
        value."""
        super().__init__('std_logic_vector', StdLogic(bit_default))

    def get_defs(self):
        """Returns the type definition(s) for this type as a list of strings
        representing lines of code."""
        return []

    def gather_members(self, count=None):
        """Yields all members of this type as `(path, type, count)`
        three-tuples. `path` is a list of `str`ings and `int`s, where a
        `str`ing means the name of a record member and an int means an array
        index. `type` is a primitive type. `count` is used for the number of
        bits in `std_logic_vector`s. Incomplete array types need an input
        `count` as well for the number of elements in the vector/array."""
        if count is None:
            raise ValueError('count must not be None for an incomplete array')
        yield [], self, count

    @staticmethod
    def get_range(count, offset=0):
        """Returns the code for a range of this array type of `count`
        elements starting at `offset`. Whether the range is ascending
        or descending depends on the type."""
        high, low = _count_and_offset_to_high_and_low(count, offset)
        return '%s downto %s' % (high, low)

    @property
    def primitive(self):
        """Indicates whether this is a primitive type."""
        return True

    def __str__(self):
        """Returns the name of this type, including suffix."""
        return self.name


class SizedArray(_Base):
    """Representation of a complete (fixed-size) array type."""

    def __init__(self, name, typ, count_or_default):
        """Completes the given incomplete array type by assigning a size to it,
        or constructs a sized array with elements of the given type.

        `count_or_default` can take three kinds of values:

         - `str` surrounded in double quotes: the array type must be an
           `std_logic_vector`, which defaults to the given bit string.
         - `int` or other `str`: the array has the given number of elements,
           which all default to the element type's default using an `others`
           statement.
         - an iterable or default values.
        """
        if not typ.incomplete:
            typ = Array(typ.name, typ, True)

        self._default_def = None
        if (isinstance(count_or_default, str)
                and count_or_default[0] == '"'
                and count_or_default[-1] == '"'):
            super().__init__(name, count_or_default)
            self._count = len(count_or_default) - 2
        elif isinstance(count_or_default, (int, str)):
            super().__init__(name, typ.default)
            self._count = count_or_default
        else:
            count_or_default = list(count_or_default)
            self._count = len(count_or_default)
            default = '(%s)' % ',@'.join(
                ('%d => %s' % x for x in enumerate(count_or_default)))
            if name is None:
                super().__init__(name, default)
            else:
                super().__init__(name, name.upper() + '_RESET')
                self._default_def = default

        self._array_type = typ

    @property
    def array_type(self):
        """Returns the underlying array type."""
        return self._array_type

    @property
    def element_type(self):
        """Returns the underlying element type."""
        return self._array_type.element_type

    @property
    def count(self):
        """Returns the number of array elements in this array subtype."""
        return self._count

    @property
    def default_def(self):
        """Returns `None` if this type has a simple default value (inline), or
        returns the complex default value otherwise. In the latter case,
        `default` returns the name of the constant that the complex default
        value is assigned to."""
        return self._default_def

    def get_range(self, count, offset=0):
        """Returns the code for a range of this array type of `count`
        elements starting at `offset`. Whether the range is ascending
        or descending depends on the type."""
        return self._array_type.get_range(count, offset)

    def __len__(self):
        """Returns the number of bits in this type."""
        return self._count * len(self.element_type)

    def get_defs(self):
        """Returns the type definition(s) for this type as a list of strings
        representing lines of code."""
        defs = ['subtype %s is %s(%s);' % (
            self, self.array_type, self.array_type.get_range(self.count))]
        if self._default_def is not None:
            defs.append('constant %s : %s@:= %s;' % (
                self.default, self, self._default_def))
        return defs

    def gather_types(self, into=None):
        """Gather all the types needed by this type into an ordered dict from
        name to type."""
        into = self.array_type.gather_types(into)
        return super().gather_types(into)

    def gather_members(self, _=None):
        """Yields all members of this type as `(path, type, count)`
        three-tuples. `path` is a list of `str`ings and `int`s, where a
        `str`ing means the name of a record member and an int means an array
        index. `type` is a primitive type. `count` is used for the number of
        bits in `std_logic_vector`s. Incomplete array types need an input
        `count` as well for the number of elements in the vector/array."""
        return self.array_type.gather_members(self._count)

    def __eq__(self, other):
        if not super().__eq__(other):
            return False
        if self.array_type != other.array_type:
            return False
        if self.count != other.count:
            return False
        if self.default_def != other.default_def:
            return False
        return True


class Slice:
    """Representation of an arbitrarily sized array slice."""

    def __init__(self, element_type, count):
        """Constructs a slice."""
        super().__init__()
        self._element_type = element_type
        self._count = count

    @property
    def element_type(self):
        """Returns the underlying element type."""
        return self._element_type

    @property
    def count(self):
        """Returns the number of elements in the slice. This may be a string if
        the count is a VHDL expression."""
        return self._count

    def __str__(self):
        return '<slice of %s>' % self.element_type


class Record(_Base):
    """Representation of a record type."""

    def __init__(self, name, *elements):
        """Constructs a record type from the given elements. Elements passed
        to `elements` must be N-tuples, which are just passed to
        `append()`."""
        super().__init__(name, name.upper() + '_RESET')
        self._elements = []
        self._names = set()
        for args in elements:
            self.append(*args)

    def append(self, name, typ, arg=None):
        """Adds an element to the record.

        If `typ` is an incomplete array, it is auto-completed with the array
        size, bit string (for `std_logic_vector`s only), or iterable of default
        values specified by `arg`. Otherwise, `arg` optionally specifies an
        override for the default value."""
        if name in self._names:
            raise ValueError('record entry name conflict: %s' % name)
        self._names.add(name)
        count = None
        if typ.incomplete:
            expanded = SizedArray('%s_%s' % (self.name, name), typ, arg)
            default = expanded.default
            if default.isupper():
                typ = expanded
            else:
                count = expanded.count
        elif arg is not None:
            default = arg
        else:
            default = typ.default
        self._elements.append((name, typ, count, default))

    def get_element(self, name):
        """Returns the type of the element going by the given name, or raises
        a `ValueError` if the name does not exist.."""
        for current_name, typ, *_ in self._elements:
            if current_name == name:
                return typ
        raise ValueError('record does not have an element named %s' % name)

    @property
    def elements(self):
        """Returns a tuple of (name, type, count, default) four-tuples
        representing all the entries of this record."""
        return tuple(self._elements)

    def __len__(self):
        """Returns the number of bits in this type."""
        return sum((
            len(typ) if count is None else len(typ.element_type) * count
            for _, typ, count, _ in self._elements))

    def get_defs(self):
        """Returns the type definition(s) for this type as a list of strings
        representing lines of code."""
        defs = ['type %s is record' % self]
        for name, typ, count, _ in self._elements:
            if count is None:
                defs.append('  %s : %s;' % (name, typ))
            else:
                defs.append('  %s : %s(%s);' % (name, typ, typ.get_range(count)))
        defs.append('end record;')
        defs.append('constant %s : %s := (' % (self.default, self))
        for name, _, _, default in self._elements:
            defs.append('  %s => %s,' % (name, default))
        defs[-1] = defs[-1][:-1]
        defs.append(');')
        return defs

    def gather_types(self, into=None):
        """Gather all the types needed by this type into an ordered dict from
        name to type."""
        if into is None:
            into = OrderedDict()
        for _, element_type, _, _ in self._elements:
            into = element_type.gather_types(into)
        return super().gather_types(into)

    def gather_members(self, _=None):
        """Yields all members of this type as `(path, type, count)`
        three-tuples. `path` is a list of `str`ings and `int`s, where a
        `str`ing means the name of a record member and an int means an array
        index. `type` is a primitive type. `count` is used for the number of
        bits in `std_logic_vector`s. Incomplete array types need an input
        `count` as well for the number of elements in the vector/array."""
        for name, typ, count, _ in self._elements:
            for subpath, subtype, subcount in typ.gather_members(count):
                yield [name] + subpath, subtype, subcount

    def __eq__(self, other):
        if not super().__eq__(other):
            return False
        if self.elements != other.elements:
            return False
        return True


class Object:
    """Base class for representing a VHDL object."""

    def __init__(self, name, typ, path=None, offset=None):
        """Represents an object with the given VHDL name and the given type.

        Normally, the array/record hierarchy present in the VHDL world (taken
        from `typ`) is mimicked in the Python world. However, it sometimes
        helps to abstract some of the VHDL structure away. This can be done
        with the `path` and `offset` parameters.

        The basic idea is that the `path` object instructs the object how to
        construct the VHDL identifier path and array indices based on input in
        the Python world. Currently, this input is restricted to indexation and
        slicing, so it's not possible to emulate a record that does not exist
        in VHDL.

        Specifically, the `path` object must be a list with the following types
        of entries:

         - A string represents a record entry that exists in the VHDL world but
           is hidden in the Python world. It is appended to the identifier path
           when all preceding array indexations have been performed. The string
           can also include array indexations of the record member if needed.
         - A two-tuple of a scalar type and either an empty list of a list with
           a single `None` entry represents an array that does not exist in the
           VHDL world but is expected by the users of this Python object. The
           indexation operator becomes no-op (it just strips the `path` entry
           off), while slicing uses the `(<range> => <name>)` syntax. The
           type's `get_range()` method is used to construct the range to get
           the correct direction for the type.
         - A two-tuple of an array type and a list of integers represents an
           array that is both expected by Python code and is present in VHDL.
           The integers in the list represent the sizes of each (remaining)
           dimension of the array. Note that the array is always
           one-dimensional in VHDL; the indices specified in the Python world
           are simply multiply-added to the appropriate sizes to make the array
           appear multidimensional. The `offset` parameter is used to track the
           offset induced by previous indexations.

        Any string path entries are suffixed to the name immediately, since
        they don't require any operation from the user. It's also legal to
        specify only a path (`name = None`) if `path` starts with such entries.
        """
        super().__init__()
        name_entries = []
        if name is not None:
            name_entries.append(name)
        if path is None:
            path = []
        else:
            path = list(path)
        while path:
            if not isinstance(path[0], str):
                break
            name_entries.append(path.pop(0))
        if not name_entries:
            raise ValueError('object does not have a name')
        self._name = '.'.join(name_entries)
        self._final_type = typ
        if path:
            self._ignore_index = False
            (self._current_type, self._array_sizes), *self._path = path
            if not self._array_sizes or self._array_sizes[0] is None:
                self._array_sizes = []
                self._ignore_index = True
            self._abstracted = True
        else:
            self._current_type = typ
            self._array_sizes = []
            self._path = []
            self._abstracted = False
            self._ignore_index = not isinstance(typ, (Array, SizedArray))
        if offset is None:
            self._offset = expr()
            self._multi_dim = False
        else:
            self._offset = expr(offset)
            self._multi_dim = True

    @property
    def name(self):
        """Returns the name of this object."""
        return self._name

    @property
    def typ(self):
        """Returns the type of this object."""
        return self._current_type

    @property
    def abstracted(self):
        """Returns whether this object is an abstraction of a VHDL object with
        a different structure."""
        return self._abstracted

    def __str__(self):
        if self._multi_dim:
            size = 1
            for dim in self._array_sizes:
                size *= dim
            return '%s(%s)' % (
                self._name,
                self.typ.get_range(size, self._offset))
        return self.name

    def __getattr__(self, name):
        if not isinstance(self._current_type, Record):
            raise AttributeError('%s is not a record' % self)
        try:
            typ = self.typ.get_element(name)
        except ValueError:
            typ = None
        if typ is None:
            raise AttributeError('record does not have an element named %s' % name)
        return Object('%s.%s' % (self.name, name), typ)

    def __getitem__(self, index):
        remaining_sizes = self._array_sizes[1:]
        stride = 1
        for dim in remaining_sizes:
            stride *= dim

        if isinstance(index, tuple):
            offset, count = index

            if self._ignore_index:
                return Object(
                    '(%s => %s)' % (self.typ.get_range(count), self.name),
                    Slice(self.typ, count))

            offset = self._offset + expr(offset) * stride
            count = expr(count) * stride

            return Object(
                '%s(%s)' % (self.name, self.typ.get_range(count, offset)),
                Slice(self.typ.element_type, count))

        if self._ignore_index:
            return Object(
                self.name,
                self._final_type,
                self._path)

        if remaining_sizes:
            return Object(
                self.name,
                self._final_type,
                [(self.typ, remaining_sizes)] + self._path,
                self._offset + expr(index) * stride)

        return Object(
            '%s(%s)' % (self.name, self._offset + index),
            self._final_type if self._abstracted else self.typ.element_type,
            self._path)


def gather_defs(*types):
    """Returns the type definition(s) for the given types as a list of
    strings representing lines of code."""
    all_types = None
    for typ in types:
        all_types = typ.gather_types(all_types)
    if all_types is None:
        return []
    defs = []
    for typ in all_types.values():
        defs.extend(typ.get_defs())
    return defs


std_logic = StdLogic() #pylint: disable=C0103
std_logic_vector = StdLogicVector() #pylint: disable=C0103
natural = Natural() #pylint: disable=C0103
boolean = Boolean() #pylint: disable=C0103
