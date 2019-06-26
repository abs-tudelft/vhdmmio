"""Module for generating VHDL code for register files."""

import os
from collections import OrderedDict
from enum import Enum
from ..template import TemplateEngine
from .match import match_template
from .types import Array

_BUS_REQ_FIELD_TEMPLATE = """
@ ${'r': 'Read', 'w': 'Write'}[dir]$ logic for $desc$
$if defined('LOOKAHEAD')
if $dir$_lreq then
$ LOOKAHEAD
end if;
$endif
$if defined('NORMAL')
if $dir$_req then
$ NORMAL
end if;
$endif
"""

_BUS_REQ_BOILERPLATE_TEMPLATE = """
$block BEFORE_READ
$if cur_cnt > 1
@ Read logic for block $blk$ of $desc$
$else
@ Read logic for $desc$
$endif
$endblock

$block AFTER_READ
if r_req then
  r_data := r_hold($bw*blk + bw-1$ downto $bw*blk$);
$if cur_cnt > 1
$if blk == 0
  r_multi := '1';
$else
  if r_multi = '1' then
    r_ack := true;
  else
    r_nack := true;
  end if;
$endif
$endif
$if blk == cur_cnt - 1
  r_multi := '0';
$endif
end if;
$if blk == 0 and read_tag is not None
if r_defer then
  r_dtag := $read_tag$;
end if;
$endif
$endblock

$block BEFORE_WRITE
$if cur_cnt > 1
@ Write logic for block $blk$ of $desc$
$else
@ Write logic for $desc$
$endif
if w_req then
  w_hold($bw*blk + bw-1$ downto $bw*blk$) := w_data;
  w_hstb($bw*blk + bw-1$ downto $bw*blk$) := w_strb;
  w_multi := '$'1' if blk < cur_cnt - 1 else '0'$';
end if;
$endblock

$block AFTER_WRITE
$if blk == cur_cnt - 1 and write_tag is not None
if w_defer then
  w_dtag := $write_tag$;
end if;
$endif
$endblock

$if dir == 'r'
$if pos == 'before'
$BEFORE_READ
$else
$AFTER_READ
$endif
$else
$if pos == 'before'
$BEFORE_WRITE
$else
$AFTER_WRITE
$endif
$endif
"""

class _Decoder:
    """Builder class for address decoders."""

    def __init__(self, address, num_bits, optimize=False):
        """Constructs an address decoder builder. The address decoder will
        match the address signal or variable named by `address`, which must be
        an `std_logic_vector(num_bits - 1 downto 0)`. If `optimize` is set,
        the action for any address for which no action is specified is
        interpreted as don't care, versus the default no-operation behavior."""
        super().__init__()
        self._num_bits = num_bits
        self._optimize = optimize
        self._tple = TemplateEngine()
        self._tple['address'] = address
        self._addresses = set()

    def add_action(self, block, address, mask=0):
        """Registers the given code block for execution when the address
        input matches `address`, with any high bits in `mask` masked *out*."""
        #if '12796' in block:
            #raise ValueError('what')
        self._addresses.add((address, mask))
        self._tple.append_block('ADDR_0x%X' % address, block)

    def generate(self):
        """Generates the address decoder."""
        if not self._addresses:
            return None
        return self._tple.apply_str_to_str(
            match_template(
                self._num_bits,
                self._addresses,
                self._optimize),
            postprocess=False)

    def append_to_template(self, template_engine, key, comment):
        """Appends this decoder to the given template engine as a block,
        prefixing the given comment."""
        block = self.generate()
        if block is None:
            return
        template_engine.append_block(key, '@ ' + comment, block)


class _InterfaceObject:
    """Wrapper for VHDL interface objects.

    The goal of this class is to abstract the nested record/array structure
    generated for the user interface into the two array accesses understood by
    the register generation logic: the first being indexation into repeated
    objects, the second being indexation of the (bit) vector requested by the
    register generation logic. Both of these can be `None` to indicate that
    the objects are not vectors, but to keep usage uniform, indexation is
    required anyway.

    As an example of what this all means, let's say that some field wants to
    connect to user logic through an 8-bit `std_logic_vector` input named
    `data`. The field is named `foo`, and is itself repeated 4 times. It is
    grouped into `bar`. This results in the following:

    ```vhdl
    type regfile_f_foo_i_type is record
      data : std_logic_vector(7 downto 0);
    end record;
    type regfile_f_foo_i_array is array (natural range <>) of regfile_f_foo_i_type;
    type regfile_g_bar_i_type is record
      foo : regfile_f_foo_i_array(0 to <obj_cnt>-1);
    end record;
    g_bar_i : in regfile_g_bar_i_type;
    ```

    But the same field can also be generated in different ways based on user
    preference. For instance, it can be flattened and not grouped at all, in
    which case this happens:

    ```
    f_foo_data : in std_logic_vector(31 downto 0);
    ```

    In both cases, we would like to be able to select for instance the low
    nibble of the second field using just

    ```
    data[1][0, 4]
    ```

    where the first `1` selects the field, and the `0, 4` are the offset and
    slice width respectively. We don't use the usual Pythonic slice notation
    because those values can all be VHDL expression strings as well. This
    should become `g_bar_i.foo(1).data(3 downto 0)` in the first case, and
    `f_foo_data(11 downto 8)` in the second case (this is done by casting to a
    string).

    The way in which the signal is to be selected is described through an
    "identifier path" list and a name. The name holds the identifier of the
    object parsed thus far; it is what's returned by `__str__`. The path
    indicates what is yet to be parsed in the form of a list that can have the
    following entries:

     - a string: this is added to the path with a `.` in front for record entry
       access. It's done implicitly by this unit, so it abstracts the record
       levels away.
     - a two-tuple of a `.types` type and a list of sizes: this represents an
       array, which is added to the path when the user indexes/slices the
       object. The list of sizes is interpreted as the dimensions of the array,
       but the array itself is flattened in VHDL (so some multiply-adding is in
       order). The list of sizes must be at least one entry long. For slicing,
       the type's `get_range()` method is used to get the range. An integer
       offset passed at initialization is added to the offset parameter, so the
       offset introduced by previously indexed dimensions can be considered.
       The list of sizes can also be `[]` or `[None]` to indicate that the
       user logic expects to need to index something, but there isn't actually
       an array in VHDL. In this case, normal indexation is ignored, slicing is
       expanded to `(<range> => <name>)`.

    When the last indexation is performed, an object wrapper from the `.types`
    submodule is returned based on a given type. This allows complex types to
    be abstracted in the same way."""

    def __init__(self, name, id_path, typ, offset=None):
        """Creates a VHDL interface object wrapper."""
        super().__init__()
        name_entries = [name]
        while id_path:
            if not isinstance(entry[0], str):
                break
            entries.append(id_path.pop(0))
        if not id_path:
            raise ValueError('need at least one array specifier in id_path')
        self._name = '.'.join(name_entries)
        self._id_path = id_path
        self._type = typ
        self._offset = offset

    def __str__(self):
        if self._offset is not None:
            size = 1
            for dim in self._id_path[0][1]:
                size *= dim
            return '%s(%s)' % (
                self._name,
                self._id_path[0][0].get_range(self._offset, size))
        return self._name

    def _index(self, index):
        if isinstance(entry[0], int):
            if not self._id_path[0] or self._id_path[0][0] is None:
                return _InterfaceObject(
                    self._name,
                    self._id_path[1:],
                    self._type)
            return _InterfaceObject(


    def __getitem__(self, index):
        if isinstance(index, tuple):
            offset, count = index
            return self._slice(offset, count)
        return self._index(index)


class _Interface:
    """Builder class for the register file interface, either the generics or
    the ports."""

    def __init__(self, type_namespace, default_group=False, default_flatten='never'):
        super().__init__()
        self._type_namespace = type_namespace
        self._default_group = default_group
        self._default_flatten = default_flatten
        self._types = []

        # (prefix, name) -> (comment, [descs], OrderedDict: full_name -> typ)
        self._decls = OrderedDict()

    def add(self,
            obj_name, obj_desc, obj_type, obj_cnt,
            sig_name, sig_mode, sig_type, sig_cnt,
            group=None, flatten=None):
        """Registers a signal or generic.

         - `obj_name`: the name of the object (field, register, interrupt,
           etc.) that the signal/generic belongs to. Must be unique within the
           object type class, and must be a valid identifier.
         - `obj_desc`: friendly description for the above, preferably ending in
           a period and starting lowercase, such as `'field <name>: <brief>'`.
           It must be unique for this object, so it should include the name and
           the object type in it.
         - `obj_type`: a single lowercase character identifying the object type
           class: `'f'` for fields, `'i'` for interrupts, etc.
         - `obj_cnt`: specifies whether the object is a scalar or a vector.
           If a vector, specify the number of entries in it as an int. If a
           scalar, specify `None`.
         - `sig_name`: name of the interface signal for this object. Needs only
           be unique within the scope of the object it belongs to, but should
           not contain underscores, be uppercase, or consist of only a single
           character.
         - `sig_mode`: I/O mode. `'i'` for input signals, `'o'` for output
           signals, `'g'` for generics.
         - `sig_type`: type class from the `.types` submodule, including the
           appropriate default value for the signal.
         - `sig_cnt`: if `sig_type` is an incomplete array, specify the size
           of the array here. Leave `None` otherwise.
         - `group`: specifies whether this object/signal should be grouped in a
           record with others. If yes, the group name should be specified,
           which must be a valid identifier. If no, specify `False`. To use the
           default value specified at initialization-time of this builder,
           leave `None`.
         - `flatten`: specifies the flattening mode using a string, see below.
           Specify `None` to use the default value specified at
           initialization-time.

        Returns an object that abstracts the VHDL signal. The object must
        always first be indexed by the object index, even if the object is not
        a vector (the index is just ignored in this case). The index can be an
        integer or a string representing a VHDL expression. The resuling object
        can be cast to a string to get the VHDL identifier path for the entire
        signal. If the signal is itself a vector (`sig_cnt` is not `None`), it
        *can* be indexed in the same way again to get a single element of the
        signal vector, or it can be sliced by indexing like `[offset, count]`
        to get a slice of size `count`, offset by `offset`. Performing
        indexation on a scalar is also allowed. A single index is no-op, while
        a slice returns `(<range> => <identifier.path>)` to get a vector again;
        the range is descending for `std_logic` and ascending otherwise. A
        singular indexation returns an object from the `.types` submodule to
        further descend into enclosed records and whatnot.

        In the generated VHDL code, signals with matching `group` are grouped
        together in a record (one record for each mode). If not flattened,
        signals belonging to a single object are also grouped in a record,
        which is turned into an array of records if the object is a vector.
        These records can be flattened away, in which case the signals
        themselves become arrays over the object indices if the object is a
        vector. If the signal itself is also an array, it becomes an array of
        arrays if `flatten='record'` or a single array sized NxM if
        `flatten='all'`. This behavior is shown schematically below.

        Grouped, `flatten='never'`:

        ```
        @ Interface group for:
        @  - <obj_desc>
        g_<group>_<sig_mode> : <dir> <rname>_g_<group>_<sig_mode>_type;
          -- is record:
          -- .<obj_type>_<obj_name> :
          --     <rname>_<obj_type>_<obj_name>_<sig_mode>_array(0 to <obj_cnt>-1);
          --   -- is array of record:
          --   -- .<sig_name> : <sig_type>(<sig_cnt>-1 downto 0);
          --   -- .<sig_name> : <sig_type>;
          -- .<obj_type>_<obj_name> : <rname>_<obj_type>_<obj_name>_<sig_mode>_type;
          --   -- is record:
          --   -- .<sig_name> : <sig_type>(<sig_cnt>-1 downto 0);
          --   -- .<sig_name> : <sig_type>;
        ```

        Grouped, `flatten='record'`:

        ```
        @ Interface group for:
        @  - <obj_desc>
        g_<group>_<sig_mode> : <dir> <rname>_g_<group>_<sig_mode>_type;
          -- .<obj_type>_<obj_name>_<sig_name> :
          --     <rname>_<obj_type>_<obj_name>_<sig_name>_array(0 to <obj_cnt>-1);
          --   -- is array of <sig_type>(<sig_cnt>-1 downto 0)
          -- .<obj_type>_<obj_name>_<sig_name> :
          --     <rname>_<obj_type>_<obj_name>_<sig_name>_array(0 to <obj_cnt>-1);
          --   -- is array of <sig_type>
          -- .<obj_type>_<obj_name>_<sig_name> : <sig_type>(<obj_cnt>-1 downto 0);
          -- .<obj_type>_<obj_name>_<sig_name> : <sig_type>;
        ```

        Grouped, `flatten='all'`:

        ```
        @ Interface group for:
        @  - <obj_desc>
        g_<group>_<sig_mode> : <dir> <rname>_g_<group>_<sig_mode>_type;
          -- .<obj_type>_<obj_name>_<sig_name> : <sig_type>(<obj_cnt>*<sig_cnt>-1 downto 0);
          -- .<obj_type>_<obj_name>_<sig_name> : <sig_type>(<obj_cnt>-1 downto 0);
          -- .<obj_type>_<obj_name>_<sig_name> : <sig_type>(<sig_cnt>-1 downto 0);
          -- .<obj_type>_<obj_name>_<sig_name> : <sig_type>;
        ```

        Not grouped, `flatten='never'`:

        ```
        @ Interface for <obj_desc>
        <obj_type>_<obj_name>_<sig_mode> : <dir>
            <rname>_<obj_type>_<obj_name>_<sig_mode>_array(0 to <obj_cnt>-1);
          -- .<sig_name> : <sig_type>(<sig_cnt>-1 downto 0);
          -- .<sig_name> : <sig_type>;
        <obj_type>_<obj_name>_<sig_mode> : <dir>
            <rname>_<obj_type>_<obj_name>_<sig_mode>_type;
          -- .<sig_name> : <sig_type>(<sig_cnt>-1 downto 0);
          -- .<sig_name> : <sig_type>;
        ```

        Not grouped, `flatten='record'`:

        ```
        @ Interface for <obj_desc>
        <obj_type>_<obj_name>_<sig_name> : <dir>
            <rname>_<obj_type>_<obj_name>_<sig_name>_array(0 to <obj_cnt>-1);
          -- is array of <sig_type>(<sig_cnt>-1 downto 0)
        <obj_type>_<obj_name>_<sig_name> : <dir>
            <rname>_<obj_type>_<obj_name>_<sig_name>_array(0 to <obj_cnt>-1);
          -- is array of <sig_type>
        <obj_type>_<obj_name>_<sig_name> : <dir> <sig_type>(<sig_cnt>-1 downto 0);
        <obj_type>_<obj_name>_<sig_name> : <dir> <sig_type>;
        ```

        Not grouped, `flatten='all'`:

        ```
        @ Interface for <obj_desc>
        <obj_type>_<obj_name>_<sig_name> : <dir> <sig_type>(<obj_cnt>*<sig_cnt>-1 downto 0);
        <obj_type>_<obj_name>_<sig_name> : <dir> <sig_type>(<obj_cnt>-1 downto 0);
        <obj_type>_<obj_name>_<sig_name> : <dir> <sig_type>(<sig_cnt>-1 downto 0);
        <obj_type>_<obj_name>_<sig_name> : <dir> <sig_type>;
        ```"""

        # Substitute defaults for group/flatten.
        if group is None:
            group = self._default_group
        if flatten is None:
            flatten = self._default_flatten

        # Check input.
        if sig_cnt is None and sig_type.incomplete:
            raise ValueError(
                'signal type is an incomplete array, but signal count is None')
        if sig_cnt is not None and not sig_type.incomplete:
            raise ValueError(
                'signal count is not None, but signal type is not an incomplete array')

        # Figure out the naming and types for the object record and/or signal,
        # without considering grouping:
        #
        #  - `new_name`: the name of the outermost signal, that will become a
        #    port or a group record entry.
        #  - `new_type`: type for the above.
        #  - `new_cnt`: array size for the above, or `None` for scalar.
        #  - `new_entry_name`: name for the signal entry within the object
        #    record, or `None` if flattened.
        #  - `new_entry_type`: type for the above.
        #  - `new_entry_cnt`: array size for the above, or `None` for scalar.
        #  - `el_id_path`: instructions for the identifier path constructor
        #    object. String entries mean indexation of the above scope using
        #    a `.`. Two-tuples are used for array indexation.


        An integer means that an index/slice must be consumed and
        #    used to index the current object. `True` and `False` also mean
        #    that an index/slice must be consumed, but indices must be ignored,
        #    and slices must use `(0 to count-1 => ...)` syntax for `False` and
        #    `(count-1 downto 0 => ...)` syntax for `True`. A tuple of integers
        #    represents multiple-indexation/slicing for emulating N-dimensional
        #    arrays.
        #  - `el_type`: type that remains after all `el_id_path` operations have
        #    been performed.
        if flatten == 'never':
            new_name = '_'.join((obj_type, obj_name, sig_mode))
            new_type = Record('_'.join((self._type_namespace, new_name)))
            if group is not None:
                new_name = '_'.join((obj_type, obj_name))
            if obj_cnt is not None:
                new_type = Array(new_type.name, new_type)
            new_cnt = obj_cnt
            new_entry_name = sig_name
            new_entry_type = sig_type
            new_entry_cnt = sig_cnt
            el_id_path = [new_name, new_cnt, new_entry_name, new_entry_cnt]
        else:
            new_name = '_'.join((obj_type, obj_name, sig_name))
            if flatten == 'record':
                new_type = sig_type

                if obj_cnt is not None:
                    if sig_cnt is not None:
                        new_type = SizedArray(
                            '_'.join((self._type_namespace, obj_type, obj_name, sig_name>)),
                            new_type, sig_cnt)
                    new_type = Array(new_type.name, new_type)
                    new_cnt = obj_cnt
                else:
                    new_cnt = sig_cnt

                if sig_cnt is not None and not new_type.incomplete:
                el_id_path = [new_name, new_cnt, sig_cnt]
            elif flatten == 'all':
                new_type = sig_type
                new_cnt = None
                el_id_path = [new_name, None, None]
                if obj_cnt is not None or sig_cnt is not None:
                    if not new_type.incomplete:
                        new_type = Array(new_type.name, new_type)
                    new_cnt = 1
                    el_id_path = [new_name]
                    for cur_cnt in [obj_cnt, sig_cnt]:
                        if cur_cnt is not None:
                            new_cnt *= cur_cnt
                            el_id_path.append(cur_cnt)
                        else:
                            el_id_path.append(1)
            new_entry_name = None
            new_entry_type = None
            new_entry_cnt = None
        if sig_type.incomplete:
            el_type = sig_type.element_type
        else:
            el_type = sig_type

        # Find the type of the toplevel signal in the interface if it already
        # exists so we can append to it (it should be a record in this case),
        # or add a new signal per the `new_*` specifications.
        if group is not None:
            decl_key = ('g', group)
            header = 'Interface group for:'
        else:
            decl_key = (obj_type, obj_name)
            header = 'Interface for ' + obj_desc
        comment, descs, signals = self._decls.get(
            decl_key, (header, [], OrderedDict()))
        self._decls[decl_key] = (comment, descs, signals)
        if group is not None:
            descs.append(obj_desc)

        # If the signal needs to be grouped, see if the group record already
        # exists. If it does, add the `new_*` signal to it. Otherwise, make a
        # new record and add the `new_*` signal to that. If we're not grouping,
        # add the `new_*` signal directly to the signal dict for this block.
        if group is not None:
            group_name = '_'.join(('g', group, sig_mode))

            if sig_mode == 'g':
                group_name = group_name.upper()

            el_id_path.insert(0, group_name)

            group_type, group_cnt = signals.get(group_name, (Record(), None))
            signals[group_name] = (group_type, group_cnt)

            assert isinstance(group_type, Record)
            assert group_cnt is None
            try:
                cur_type = group_type.get_element(new_name)
            except ValueError:
                group_type.append(new_name, new_type, new_cnt)
                cur_type = new_type
        else:
            if sig_mode == 'g':
                new_name = new_name.upper()

            cur_type, cur_cnt = signals.get(new_name, (new_type, new_cnt))
            signals[new_name] = (cur_type, cur_cnt)

        # If `new_type` is a record that we need to add something to, do so
        # now.
        if new_entry_name is not None:
            if isinstance(cur_type, Array):
                record_type = cur_type.element_type
            else:
                record_type = cur_type
            assert isinstance(cur_type, Record)
            record_type.append(new_entry_name, new_entry_type, new_entry_cnt)



class RegfileGenerator:
    """VHDL generator for register files."""

    def __init__(self, regfile):
        """Constructs a VHDL generator for the given register file."""
        super().__init__()
        self._regfile = regfile

        # Main template engine, used to generate the actual VHDL files.
        self._tple = TemplateEngine()
        self._tple['r'] = regfile

        # Interface variables.
        self._public_types = []
        self._generic_decls = OrderedDict()
        self._port_decls = OrderedDict()

        # Address decoder builders.
        self._read_decoder = _Decoder('r_addr', 32)
        self._read_tag_decoder = _Decoder('r_rtag', regfile.read_tag_width)
        self._write_decoder = _Decoder('w_addr', 32)
        self._write_tag_decoder = _Decoder('w_rtag', regfile.write_tag_width)

        # Generate code for interrupts.
        for interrupt in regfile.interrupts:
            interrupt.generate_vhdl(self)

        # Generate boilerplate register access code before field code.
        for register in regfile.registers:
            self._add_register_boilerplate(register, 'before')

        # Generate code for fields.
        for field_descriptor in regfile.field_descriptors:
            field_descriptor.logic.generate_vhdl(self)

        # Generate boilerplate register access code before after code.
        for register in regfile.registers:
            self._add_register_boilerplate(register, 'after')

        # Add the decoders to the main template engine.
        self._read_decoder.append_to_template(
            self._tple, 'FIELD_LOGIC_READ',
            'Read address decoder.')
        self._read_tag_decoder.append_to_template(
            self._tple, 'FIELD_LOGIC_READ_TAG',
            'Deferred read tag decoder.')
        self._write_decoder.append_to_template(
            self._tple, 'FIELD_LOGIC_WRITE',
            'Write address decoder.')
        self._write_tag_decoder.append_to_template(
            self._tple, 'FIELD_LOGIC_WRITE_TAG',
            'Deferred write tag decoder.')

    def generate_files(self, output_directory):
        """Generates the files for this register file in the specified
        directory."""
        self._tple.apply_file_to_file(
            os.path.dirname(__file__) + os.sep + 'entity.template.vhd',
            output_directory + os.sep + self._regfile.meta.name + '.vhd',
            comment='-- ')
        self._tple.apply_file_to_file(
            os.path.dirname(__file__) + os.sep + 'package.template.vhd',
            output_directory + os.sep + self._regfile.meta.name + '_pkg.vhd',
            comment='-- ')

    @staticmethod
    def _describe_interrupt(interrupt):
        """Generates a description for an interrupt, to be used as block
        comment."""
        return '%s-sensitive interrupt %s: %s' % (
            'strobe' if interrupt.can_clear else 'level',
            interrupt.meta[None].markdown_name,
            interrupt.meta[None].markdown_brief)

    @staticmethod
    def _describe_field_descriptor(field_descriptor):
        """Generates a description for a field descriptor, to be used as block
        comment."""
        return 'field %s%s: %s' % (
            'group ' if field_descriptor.vector_count is not None else '',
            field_descriptor.meta[None].markdown_name,
            field_descriptor.meta[None].markdown_brief)

    @staticmethod
    def _describe_field(field):
        """Generates a description for a field, to be used as block comment."""
        return 'field %s: %s' % (
            field.meta.markdown_name,
            field.meta.markdown_brief)

    @staticmethod
    def _describe_register(register):
        """Generates a description for a register, to be used as block
        comment."""
        return 'register %s: %s' % (
            register.meta.markdown_name,
            register.meta.markdown_brief)

    def _add_interface(self, desc, name, typ, array, mode):
        """Adds an interface (port or generic) to the generated entity. `desc`
        must be a user-friendly string description of the interrupt or field
        that the interface belongs to; it is used as a comment. `name` must be
        a unique identifier within the entity for the interface. `typ` must be
        a `types._Base`-derived type description for the interface. `array`
        must be `None` if the interrupt/field is scalar, or the integral size
        of the array. `mode` must be `'in'`, `'out'`, or `'generic'` to select
        the interface type."""

        # If we need to make an array of signals/generics because the field or
        # interrupt we're generating for is a vector, modify the type
        # appropriately. If it is already an incomplete array, set its size
        # in-place; if it's not, build an incomplete array type around it.
        # If we don't want a vector but the user supplied an incomplete array,
        # just make an array with one entry.
        if array is not None and not typ.incomplete:
            typ = Array(typ.name, typ)
        if typ.incomplete:
            if array is None:
                array = 1

        # Store the type, so we can generate the requisite type definitions for
        # it later.
        self._public_types.append(typ)

        # Construct the generic/signal declaration and its abstracted Python
        # object representation for referring to it.
        decl, ref = {
            'generic': typ.make_generic,
            'in': typ.make_input,
            'out': typ.make_output,
        }[mode](name, array)

        # Construct the block comment from the block description and select the
        # appropriate dictionary to append to.
        if mode == 'generic':
            comment = '@ Generics for %s' % desc
            decl_dict = self._generic_decls
        else:
            comment = '@ Ports for %s' % desc
            decl_dict = self._port_decls

        # If there is no block with the specified comment yet, create one.
        # Otherwise, append to the previously created block.
        decls = decl_dict.get(comment, None)
        if decls is None:
            decl_dict[comment] = [decl]
        else:
            decls.append(decl)

        return ref

    def add_interrupt_interface(self, interrupt, name, typ, mode):
        """Registers a port or generic for the given interrupt with the
        specified (namespaced) name, VHDL type object (from `.types`), and
        mode, which must be `'in'`, `'out'`, or `'generic'`. Returns a
        pythonic object representing the interface (i.e., if the type is a
        record, it has attributes for each record entry; if it is an array, it
        can be indexed) that has a `__str__` function that converts to the VHDL
        name."""
        return self._add_interface(
            self._describe_interrupt(interrupt),
            'i_%s_%s' % (interrupt.meta.name, name),
            typ, interrupt.width, mode)

    def add_field_interface(self, field_descriptor, name, typ, mode):
        """Registers a port or generic for the given field descriptor with the
        specified (namespaced) name, VHDL type object (from `.types`), and
        mode, which must be `'in'`, `'out'`, or `'generic'`. Returns a
        pythonic object representing the interface (i.e., if the type is a
        record, it has attributes for each record entry; if it is an array, it
        can be indexed) that has a `__str__` function that converts to the VHDL
        name."""
        return self._add_interface(
            self._describe_field_descriptor(field_descriptor),
            'f_%s_%s' % (field_descriptor.meta.name, name),
            typ, field_descriptor.vector_count, mode)

    def _add_block(self, key, region, desc, block):
        if block is not None:
            self._tple.append_block(key, '@ %s for %s' % (region, desc), block)

    def _add_declarations(self, desc, private, public, body):
        """Registers declarative code blocks, expanded into respectively the
        process header, package header, and package body. `desc` is used for
        generating the comment that is placed above the blocks."""
        self._add_block('DECLARATIONS', 'Private declarations', desc, private)
        self._add_block('PACKAGE', 'Public declarations', desc, public)
        self._add_block('PACKAGE_BODY', 'Implementations', desc, body)

    def add_interrupt_declarations(self, interrupt, private=None, public=None, body=None):
        """Registers declarative code blocks for the given interrupt,
        expanded into respectively the process header, package header, and
        package body. A comment identifying the interrupt is added before the
        blocks automatically."""
        self._add_declarations(
            self._describe_interrupt(interrupt),
            private, public, body)

    def add_field_declarations(self, field_descriptor, private=None, public=None, body=None):
        """Registers declarative code blocks for the given field descriptor,
        expanded into respectively the process header, package header, and
        package body. A comment identifying the field is added before the blocks
        automatically."""
        self._add_declarations(
            self._describe_field_descriptor(field_descriptor),
            private, public, body)

    def add_interrupt_logic(self, interrupt, logic):
        """Registers the code block for the logic of the specified interrupt.
        The generated block is executed every cycle. The block must indicate
        whether the interrupt(s) is/are asserted by writing to the variable
        expanded by `$irq$`. This is an `std_logic` for scalar interrupts, and
        an `std_logic_vector` for vector interrupts. It is active high."""
        self._add_block(
            'IRQ_LOGIC', 'Interrupt logic',
            self._describe_interrupt(interrupt), logic)

    def add_field_interface_logic(self, field_descriptor, pre=None, post=None):
        """Registers code templates for the hardware interface of the specified
        field. `pre` is placed before the bus interface logic, `post` is placed
        after. These blocks are executed every cycle for each (enabled) field
        in the descriptor. The template parameter `$i$` can be used for the
        field index. A comment identifying the field is added before the blocks
        automatically."""
        tple = TemplateEngine()
        tple['desc'] = self._describe_field_descriptor(field_descriptor)
        template = '@ $position$-bus logic for $desc$\n'
        if field_descriptor.vector_count is None:
            template += '$BLOCK'
            tple['i'] = '0'
        else:
            template += 'for i in 0 to $count-1$ loop\n$ BLOCK\nend loop;'
            tple['count'] = field_descriptor.vector_count
            tple['i'] = 'i'
        if pre is not None:
            tple['position'] = 'Pre'
            tple.append_block('BLOCK', pre)
            block = tple.apply_str_to_str(template, postprocess=False)
            self._tple.append_block('FIELD_LOGIC_BEFORE', block)
        if post is not None:
            tple['position'] = 'Post'
            tple.reset_block('BLOCK')
            tple.append_block('BLOCK', post)
            block = tple.apply_str_to_str(template, postprocess=False)
            self._tple.append_block('FIELD_LOGIC_AFTER', block)

    def _add_field_bus_logic(self, field, direction, normal, lookahead, deferred):
        """Implements `add_field_read_logic()` and `add_field_write_logic()`.
        They are distinguished through `direction`, which must be `'r'` or
        `'w'`."""

        # Determine the address that the regular field logic should be
        # activated for.
        register = field.register
        address = register.address
        if direction == 'w':
            address += (1 << register.block_size) * (register.block_count - 1)
        mask = (1 << register.block_size) - 1

        # Describe the field for use in comments.
        desc = self._describe_field(field)

        # Add the normal and lookahead blocks.
        tple = TemplateEngine()
        tple['desc'] = desc
        tple['dir'] = direction
        if normal is not None:
            tple.append_block('NORMAL', '@ Access logic.', normal)
        if lookahead is not None:
            tple.append_block('LOOKAHEAD', '@ Lookahead logic.', lookahead)
        block = tple.apply_str_to_str(_BUS_REQ_FIELD_TEMPLATE, postprocess=False)
        decoder = {'r': self._read_decoder, 'w': self._write_decoder}[direction]
        decoder.add_action(block, address, mask)

        # Add the deferred block.
        if deferred is not None:
            tag = {'r': register.read_tag, 'w': register.write_tag}[direction]
            assert tag is not None and tag.startswith('"') and tag.endswith('"')
            tag = int(tag[1:-1], 2)
            decoder = {'r': self._read_tag_decoder, 'w': self._write_tag_decoder}[direction]
            decoder.add_action(
                '@ Deferred %s logic for %s\n%s' % (
                    {'r': 'read', 'w': 'write'}[direction],
                    desc, deferred),
                tag)

    def add_field_read_logic(self, field, normal, lookahead=None, deferred=None):
        """Registers code blocks for handling bus reads for the given field.
        Note that this function expects a `Field`, not a `FieldDescriptor`. The
        generator ensures that the generated code is only executed when the
        field is addressed, enabled, and the bus logic is performing the
        following actions:

         - `normal`: the bus is currently accessing the field, and the bus
           response buffers are ready to accept the read result. `r_prot` holds
           the protection flags for the read. The block can do the following
           things to interact with the bus:

            - Set `r_ack` to `true` and the bits in `r_hold` designated by the
              field's bitrange to the read result to acknowledge the request.
            - Set `r_nack` to `true` to respond with a slave error.
            - Set `r_block` to `true` to stall, IF the `can_block` flag was
              set for the field's read capabilities. In this case, the block
              will be executed again the next cycle.
            - Set `r_defer` to `true` to defer, IF the `can_defer` flag was
              set for the field's read capabilities. In this case, the request
              logic will accept the bus request and send subsequent requests
              to `lookahead` blocks, while the response logic will start
              calling the `deferred` block to get the response.
            - Nothing: the bus behaves as if the field does not exist. If there
              are no other fields in the addressed register, a decode error is
              returned.

         - `lookahead`: the bus is currently accessing the field, but the
           response logic is not ready for the result yet. This can happen
           because the response channels are still blocked or because this or
           another field deferred a previous request. It can be useful for
           fields that have a long access time. `r_prot` holds the protection
           flags for the read. The block can do the following things to
           interact with the bus:

            - Set `r_defer` to `true` to defer, IF the `can_defer` flag was
              set for the field's read capabilities. In this case, the request
              logic will accept the bus request and send subsequent requests
              to `lookahead` blocks, while the response logic will start
              calling the `deferred` block to get the response when the
              response logic does become ready.
            - Nothing: the bus logic will continue calling the lookahead block
              until the response logic is ready for the response, at which
              point it will call the `normal` block.

         - `deferred`: the `normal` or `lookahead` deferred a read in a
           preceding cycle, and the response logic is ready to accept the read
           result. Multiple accesses can be deferred this way by the same
           field; in all cases it is up to the field to memorize the associated
           protection flags if it needs them. The block can do the following
           things to interact with the bus:

            - Set `r_ack` to `true` and the bits in `r_hold` designated by the
              field's bitrange to the read result to complete the transfer.
            - Set `r_nack` to `true` to respond with a slave error.
            - Set `r_block` to `true` to stall, IF the `can_block` flag was
              set for the field's read capabilities. In this case, the block
              will be executed again the next cycle.
            - Nothing: the bus behaves as if the field does not exist. If there
              are no other fields in the addressed register, a decode error is
              returned.
        """
        self._add_field_bus_logic(field, 'r', normal, lookahead, deferred)

    def add_field_write_logic(self, field, normal, lookahead=None, deferred=None):
        """Registers code blocks for handling bus writes for the given
        field. Note that this function expects a `Field`, not a
        `FieldDescriptor`. The generator ensures that the generated code is
        only executed when the register that the field belongs to is addressed,
        enabled, and the bus logic is performing the following actions:

         - `normal`: the bus is currently writing to the register that the
           field belongs to, and the bus response buffers are ready to accept
           the write result. `w_hold` and `w_hstb` hold the data that is being
           written to the register; the field should concern itself only with
           the bits in these variables designated by the field's bitrange. The
           variables carry the following significance:

            - `w_hstb` low, `w_hold` low: bit was not written/was masked out.
            - `w_hstb` high, `w_hold` low: bit was written zero.
            - `w_hstb` high, `w_hold` high: bit was written one.

           Note that it is possible that none of the bits belonging to the
           field were actually written; if the field wishes to honor the strobe
           bits, it must do so manually. `w_prot` furthermore holds the
           protection flags for the write. The block can do the following
           things to interact with the bus:

            - Set `w_ack` to `true` to acknowledge the request.
            - Set `w_nack` to `true` to respond with a slave error.
            - Set `w_block` to `true` to stall, IF the `can_block` flag was
              set for the field's write capabilities. In this case, the block
              will be executed again the next cycle.
            - Set `w_defer` to `true` to defer, IF the `can_defer` flag was
              set for the field's write capabilities. In this case, the request
              logic will accept the bus request and send subsequent requests
              to `lookahead` blocks, while the response logic will start
              calling the `deferred` block to get the response.
            - Nothing: the bus behaves as if the field does not exist. If there
              are no other fields in the addressed register, a decode error is
              returned.

         - `lookahead`: the bus is currently accessing the field, but the
           response logic is not ready for the result yet. This can happen
           because the response channels are still blocked or because this or
           another field deferred a previous request. It can be useful for
           fields that have a long access time. `w_hold`, `w_hstb`, and
           `w_prot` carry the same significance that they do for the `normal`
           block. The block can do the following things to interact with the
           bus:

            - Set `w_defer` to `true` to defer, IF the `can_defer` flag was
              set for the field's write capabilities. In this case, the request
              logic will accept the bus request and send subsequent requests
              to `lookahead` blocks, while the response logic will start
              calling the `deferred` block to get the response when the
              response logic does become ready.
            - Nothing: the bus logic will continue calling the lookahead block
              until the response logic is ready for the response, at which
              point it will call the `normal` block.

         - `deferred`: the `normal` or `lookahead` deferred a write in a
           preceding cycle, and the response logic is ready to accept the read
           result. Multiple accesses can be deferred this way by the same
           field; in all cases it is up to the field to memorize the associated
           write data and protection flags if it still needs them. The block
           can do the following things to interact with the bus:

            - Set `w_ack` to `true` to complete the transfer.
            - Set `w_nack` to `true` to respond with a slave error.
            - Set `w_block` to `true` to stall, IF the `can_block` flag was
              set for the field's write capabilities. In this case, the block
              will be executed again the next cycle.
            - Nothing: the bus behaves as if the field does not exist. If there
              are no other fields in the addressed register, a decode error is
              returned.
        """
        self._add_field_bus_logic(field, 'w', normal, lookahead, deferred)

    def _add_register_boilerplate(self, register, position):
        """Adds the boilerplate bus logic for the given register. `position`
        indicates the relation of this function call with respect to the
        functions that add the field logic; if `'before'`, the function assumes
        that it is called before the field logic is added, if `'after'` it
        assumes after. Both variants must be called exactly once for each
        register."""
        mask = (1 << register.block_size) - 1
        tple = TemplateEngine()
        tple['pos'] = position
        tple['bw'] = register.regfile.bus_width
        tple['desc'] = self._describe_register(register)
        tple['cur_cnt'] = register.block_count
        tple['read_tag'] = register.read_tag
        tple['write_tag'] = register.write_tag
        for block_index in range(register.block_count):
            tple['blk'] = block_index
            address = register.address + (1 << register.block_size) * block_index
            if register.read_caps is not None:
                tple['dir'] = 'r'
                block = tple.apply_str_to_str(
                    _BUS_REQ_BOILERPLATE_TEMPLATE, postprocess=False)
                self._read_decoder.add_action(block, address, mask)
            if register.write_caps is not None:
                tple['dir'] = 'w'
                block = tple.apply_str_to_str(
                    _BUS_REQ_BOILERPLATE_TEMPLATE, postprocess=False)
                self._write_decoder.add_action(block, address, mask)


class VhdlGenerator:
    """Class for generating VHDL from the register file descriptions."""

    def __init__(self, regfiles, output_directory):
        for regfile in regfiles:
            RegfileGenerator(regfile).generate_files(output_directory)
        with open(os.path.dirname(__file__) + os.sep + 'vhdmmio_pkg.vhd', 'r') as in_fd:
            vhdmmio_pkg = in_fd.read()
        with open(output_directory + os.sep + 'vhdmmio_pkg.vhd', 'w') as out_fd:
            out_fd.write(vhdmmio_pkg)
