"""Submodule for generating VHDL entities."""

from collections import OrderedDict
from .types import Record, Array, SizedArray, Object, StdLogic, StdLogicVector

class Interface:
    """Builder class for a VHDL entity description."""

    def __init__(self, type_namespace):
        """Constructs an interface builder. `type_namespace` is used as a
        prefix for the VHDL type names constructed for the interface."""
        super().__init__()
        self._type_namespace = type_namespace

        # (prefix, name) -> (comment, {descs}, OrderedDict: full_name -> (typ, count, mode))
        self._decls = OrderedDict()

    def add(self,
            obj_name, obj_desc, obj_type, obj_cnt,
            sig_name, sig_mode, sig_type, sig_cnt,
            options):
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
           character. Can also be `None`, but only if records are flattened.
         - `sig_mode`: I/O mode. `'i'` for input signals, `'o'` for output
           signals, `'g'` for generics.
         - `sig_type`: type class from the `.types` submodule, including the
           appropriate default value for the signal. Defaults to `std_logic`
           or `std_logic_vector` depending on `sig_cnt` when set to `None`.
         - `sig_cnt`: if `sig_type` is an incomplete array, specify the size
           of the array here. Leave `None` otherwise.
         - `options` must be an `InterfaceOptions` object to control how the
           interface is generated. The contained `group` option specifies
           whether this object/signal should be grouped in a record with
           others. The `flatten` option specifies the flattening mode, see
           below. Specify `None` to use the default value specified at
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
        if sig_mode == 'g':
            group = options.generic_group
            flatten = options.generic_flatten
        else:
            group = options.port_group
            flatten = options.port_flatten

        # Check input.
        if sig_type is None:
            if sig_cnt is None:
                sig_type = StdLogic()
            else:
                sig_type = StdLogicVector()
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
        #  - `obj_path`: abstraction instructions for the `types.Object` return
        #    value, including name. See `types.Object` constructor for more
        #    info.
        #  - `obj_typ`: type for the above.
        if flatten == 'never':
            new_name = '_'.join((obj_type, obj_name, sig_mode))
            new_type = Record('_'.join((self._type_namespace, new_name)))
            if group is not None:
                new_name = '_'.join((obj_type, obj_name))
            if obj_cnt is not None:
                new_type = Array(new_type.name, new_type, True)
            new_cnt = obj_cnt

            new_entry_name = sig_name
            new_entry_type = sig_type
            new_entry_cnt = sig_cnt

            obj_path = [
                new_name,
                (new_type, [obj_cnt]),
                new_entry_name,
                (sig_type, [sig_cnt])]

        else:
            name_tup = (obj_type, obj_name)
            if sig_name is not None:
                name_tup += (sig_name,)
            new_name = '_'.join(name_tup)
            if flatten == 'record':
                new_type = sig_type

                if obj_cnt is not None:
                    if sig_cnt is not None:
                        type_name = '_'.join((self._type_namespace,) + name_tup)
                        new_type = SizedArray(type_name, new_type, sig_cnt)
                    new_type = Array(new_type.name, new_type, True)
                    new_cnt = obj_cnt
                else:
                    new_cnt = sig_cnt

                obj_path = [
                    new_name,
                    (new_type, [obj_cnt]),
                    (sig_type, [sig_cnt])]

            elif flatten == 'all':
                new_type = sig_type
                new_cnt = None
                obj_path = [new_name, None, None]
                if obj_cnt is not None or sig_cnt is not None:
                    if isinstance(new_type, StdLogic):
                        new_type = StdLogicVector(new_type.default[1])
                    elif not new_type.incomplete:
                        new_type = Array(new_type.name, new_type, True)
                    new_cnt = 1
                    for cur_cnt in [obj_cnt, sig_cnt]:
                        if cur_cnt is not None:
                            new_cnt *= cur_cnt

                if obj_cnt is not None and sig_cnt is not None:
                    obj_path = [
                        new_name,
                        (sig_type, [obj_cnt, sig_cnt])]
                else:
                    obj_path = [
                        new_name,
                        (new_type, [obj_cnt]),
                        (sig_type, [sig_cnt])]

            new_entry_name = None
            new_entry_type = None
            new_entry_cnt = None

        if sig_cnt is None:
            obj_typ = sig_type
        else:
            obj_typ = sig_type.element_type

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
            decl_key, (header, set(), OrderedDict()))
        self._decls[decl_key] = (comment, descs, signals)
        if group is not None:
            descs.add(obj_desc)

        # If the signal needs to be grouped, see if the group record already
        # exists. If it does, add the `new_*` signal to it. Otherwise, make a
        # new record and add the `new_*` signal to that. If we're not grouping,
        # add the `new_*` signal directly to the signal dict for this block.
        if group is not None:
            group_name = '_'.join(('g', group, sig_mode))

            if sig_mode == 'g':
                group_name = group_name.upper()

            obj_path.insert(0, group_name)

            group_type, group_cnt, group_mode = signals.get(
                group_name,
                (Record('_'.join((self._type_namespace, group_name)).lower()), None, sig_mode))
            signals[group_name] = (group_type, group_cnt, group_mode)

            assert isinstance(group_type, Record)
            assert group_cnt is None
            assert group_mode is sig_mode
            try:
                cur_type = group_type.get_element(new_name)
            except ValueError:
                group_type.append(new_name, new_type, new_cnt)
                cur_type = new_type
        else:
            if sig_mode == 'g':
                new_name = new_name.upper()
                obj_path[0] = obj_path[0].upper()

            cur_type, cur_cnt, cur_mode = signals.get(new_name, (new_type, new_cnt, sig_mode))
            signals[new_name] = (cur_type, cur_cnt, cur_mode)

        # If `new_type` is a record that we need to add something to, do so
        # now.
        if new_entry_name is not None:
            if isinstance(cur_type, Array):
                record_type = cur_type.element_type
            else:
                record_type = cur_type
            assert isinstance(record_type, Record)
            record_type.append(new_entry_name, new_entry_type, new_entry_cnt)

        return Object(None, obj_typ, obj_path)

    def generate(self, section, end_with_semicolon=True):
        """Generates the VHDL code block for this interface. `section` must be
        `'port'` or `'generic'`. `end_with_semicolon` configures whether the
        last entry must have a semicolon or not. This function returns a list
        of strings representing the code blocks."""
        blocks = []
        for comment, descs, signals in self._decls.values():
            block = []
            block.append('@ %s' % comment)
            for desc in sorted(descs):
                block.append('@  - %s' % desc)
            any_decls = False
            for name, (typ, count, mode) in signals.items():
                decl = None
                if section == 'port':
                    if mode == 'i':
                        decl, _ = typ.make_input(name, count)
                    elif mode == 'o':
                        decl, _ = typ.make_output(name, count)
                elif section == 'generic':
                    if mode == 'g':
                        decl, _ = typ.make_generic(name, count)
                if decl is None:
                    continue
                block.append(decl + ';')
                any_decls = True
            if any_decls:
                blocks.append('\n'.join(block))
        if blocks and not end_with_semicolon:
            assert blocks[-1][-1] == ';'
            blocks[-1] = blocks[-1][:-1]
        return blocks

    def gather_types(self):
        """Yields the toplevel types of all the signals used by this
        interface, for gathering all requisite typedefs."""
        for _, _, signals in self._decls.values():
            for typ, _, _ in signals.values():
                yield typ

    def gather_ports(self):
        """Yields all the inputs/outputs/generics created by this interface as
        `(mode, name, type, count)` four-tuples. `mode` is `'i'` for inputs,
        `'o'` for outputs, and `'g'` for generics. `count` is `None` if the
        type is not an incomplete array."""
        for _, _, signals in self._decls.values():
            for name, (typ, count, mode) in signals.items():
                yield mode, name, typ, count
