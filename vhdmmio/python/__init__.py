
import threading
from ..core.regfile import RegisterFile

class AccessJob:
    """Represents an optimized atomic bulk read/write/read-modify-write
    operation."""

    def __init__(self, instance):
        super().__init__()
        self._instance = instance

        # `dict((addr, count, stride) -> bit-enable)`
        # Represents the reads that have been queued up. `addr` is the base
        # address of the logical register that is to be read. `count` is the
        # number of physical registers belonging to the logical register.
        # `stride` is the amount of bytes to add to the address for every
        # subsequent physical register. `bit-enable` specifies whether side
        # effects for reading the bit are allowed, equivalent to a read being
        # explicitly requested.
        self._reads = {}

        # `dict((addr, count, stride) -> Register)`
        # Same key as `_reads`, but maps to the corresponding `Register`.
        self._read_regs = {}

        # `dict((addr, count, stride) -> data)`
        # Represents the data that has been read. Only assigned after the read
        # part of this job has completed, of course. The values are ints.
        self._read_data = None

        # `dict((addr, count, stride) -> bit-enable)`
        # Like `_reads`, but for the write strobes.
        self._write = {}

        # `dict((addr, count, stride) -> Register)`
        # Same key as `_write`, but maps to the corresponding `Register`.
        self._write_regs = {}

        # `dict((addr, count, stride) -> data)`
        # Like `_reads`, but for the write data.
        self._write_data = {}

    @classmethod
    def _expand_byte_enable(cls, byte_enable):
        """Given a list of byte enables as booleans of a power-of-two size,
        return a similar list of enables expanded to a single power-of-two-
        size-aligned access."""
        if len(byte_enable) == 1:
            return byte_enable
        low = byte_enable[:len(byte_enable)//2]
        high = byte_enable[len(byte_enable)//2:]
        if any(low):
            if any(high):
                return [True] * len(byte_enable)
            return cls._expand_byte_enable(low) + [False]*len(high)
        elif any(high):
            return [False]*len(low) + cls._expand_byte_enable(high)
        return [False] * len(byte_enable)

    def execute():
        """Executes this job, if possible."""
        if self.read_data is not None:
            raise ValueError('this job has already been executed')

        # Make sure that the fields that are not explicitly read but are part
        # of registers that do need to be read can be read without side
        # effects.
        for key, register in self._read_regs.items():
            reads = self._reads[key]
            for field in register.fields:
                mask = (1 << field.bitrange.width) - 1
                mask <<= field.bitrange.low_bit
                if not (reads & mask):
                    if not field.logic.read_is_no_op:
                        raise ValueError(
                            'register %s must be read, but contained field %s '
                            'was not requested to be read and has a read '
                            'action with side effects'
                            % (register.meta.name, field.meta.name))

        # Determine the appropriate write strobe action for each written
        # register, making sure that we don't override or cause side effects
        # for fields that should not be written.
        for key, register in self._write_regs.items():
            req_strobe = self._write[key]
            data = self._write_data[key]

            # Convert the requested strobe to a feasible strobe for systems
            # that only support aligned byte, halfword, word, etc accesses.
            bus_width = register.regfile.bus_width
            word_mask = (1 << bus_width) - 1
            strobe = 0
            for word in register.block_count:
                req_word_strobe = (req_strobe >> (word * bus_width)) & word_mask
                byte_enable = []
                for byte in range(bus_width // 8):
                    byte_enable.append(req_word_strobe & (255 << (8 * byte)))
                byte_enable = self._expand_byte_enable(byte_enable)
                word_strobe = 0
                for byte, enable in enumerate(byte_enable):
                    if enable:
                        word_strobe |= 255 << (8 * byte)
                # The last word in a multi-word access MUST be written in order
                # to execute the write.
                if word == register.block_count - 1:
                    if word_strobe is 0:
                        word_strobe = 255 << (bus_width // 8 - 1)
                strobe |= word_strobe << (word * bus_width)

            # FGSFDS


    def _field_metrics(field, block):
        """Returns the key for the internal dictionaries associated with the
        given field/block pair and the bitmask for the field without the
        shift, so representing only the vector width of the field."""
        bitr = field.bitrange
        addr = bitr.address + block * (bitr.bus_width // 8)
        count = field.register.block_count
        stride = 2**bitr.size
        key = addr, count, stride
        return key, ((1 << bitr.width) - 1)

    def _read(self, field, block):
        """Registers the given field and block for reading and return a
        function that can be used to get the value after the job. `block`
        must be an `int`, slicing is handled by `read()`."""
        if field.read_caps is None:
            raise ValueError('read to write-only field')

        key, mask = self._field_metrics(field, block)

        # Register an empty read for the field's logical register.
        if key not in self._write:
            self._write[key] = 0
            self._write_regs[key] = field.register
            self._write_data[key] = 0

        # Update the read command for the field's logical register.
        self._read[key] |= mask << field.bitrange.low_bit

        # Construct the reader object.
        def reader():
            if self._read_data is None:
                self.execute()
            data = self._read_data[key]
            data >>= field.bitrange.low_bit)
            data &= mask
            return data

        return reader

    def _modify(self, field, block, value, strobe):
        """Registers the given field and block for modification. `block` must
        be an `int`, slicing is handled by `modify()`/`write()`."""
        if field.write_caps is None:
            raise ValueError('write to read-only field')

        key, mask = self._field_metrics(field, block)

        # Desugar value and strobe.
        if isinstance(value, str):
            if len(value) != field.bitrange.width:
                raise TypeError('value bitstring does not have the right length')
            value = int(value, 2)
        else:
            value = int(value)
        value &= mask
        if isinstance(strobe, str):
            if len(strobe) != field.bitrange.width:
                raise TypeError('strobe bitstring does not have the right length')
            strobe = int(strobe, 2)
        else:
            strobe = int(strobe)
        strobe &= mask

        # If we don't set any bits, ignore the access.
        if strobe == 0:
            return

        # Register an empty write for the field's logical register.
        if key not in self._write:
            self._write[key] = 0
            self._write_regs[key] = field.register
            self._write_data[key] = 0

        # Update the write command for the field's logical register.
        strobe <<= field.bitrange.low_bit
        data <<= field.bitrange.low_bit
        self._write[key] |= strobe
        self._write_data[key] &= ~strobe
        self._write_data[key] |= data

        # No need to queue a read if we set all bits in the field.
        if strobe == mask:
            return

        # Make sure this field can be RMW'd.
        if not field.logic.can_mask_with_rmw:
            raise ValueError('read-modify-write to field that cannot be appropriately read')

        # Make sure that the register is read.
        if key not in self._read:
            self._read[key] = 0
            self._read_regs[key] = field.register

    def _field_block_indices(field, block_or_slice):
        """Desugars a slice() object for block indexing and checks that the
        index is in range."""
        nblocks = 2**(field.bitrange.size - self._instance.bus_size)
        block_or_list = block_or_slice
        if isinstance(block_or_slice, slice):
            block_or_list = list(slice.indices(nblocks))
        elif block_or_slice < 0 or block_or_slice >= nblocks:
            raise IndexError('block index out of range: %s' % block_or_slice)
        return block_or_list

    def read(self, field, block):
        """Registers the given `Field` for reading and returns a function that
        can be used to get the value after the job. `block` supports slicing;
        if it's a `slice` object a list of read functions."""
        if self._read_data is not None:
            raise ValueError('job has already been executed, cannot mutate')
        block = self._field_block_indices(field, block)
        if isinstance(block, list):
            blocks = block
            return [self._read(field, block) for block in blocks]
        return self._read(field, block)

    def modify(self, field, block, value, strobe):
        """Registers the given `Field` for modification. `value` and `strobe`
        can be integers or bit-strings of the right width. `block` supports
        slicing; if it's a `slice` then `value` and `strobe` can also be lists
        of the same size as the slice (if they're not lists, the value is
        repeated for each block)."""
        if self._read_data is not None:
            raise ValueError('job has already been executed, cannot mutate')
        block = self._field_block_indices(field, block)
        if isinstance(block, list):
            blocks = block
            if hasattr(value, '__iter__'):
                values = list(value)
                if len(values) != len(block):
                    raise TypeError('incorrect number of values specified')
            else:
                values = [value] * len(block)
            if hasattr(strobe, '__iter__'):
                strobes = list(strobe)
                if len(strobes) != len(block):
                    raise TypeError('incorrect number of strobes specified')
            else:
                strobes = [strobe] * len(block)
            for block, value, strobe in zip(blocks, values, strobes):
                self._modify(field, block, value, strobe)
        else:
            self._modify(field, block, value, strobe)

    def write(self, field, block, value):
        """Registers the given `Field` for writing. `value` can be an integer
        or a bit-string of the right width. `block` supports slicing; if it's
        a `slice` then `value` can also be a list of the same size as the slice
        (if it's not a list, the value is repeated for each block)."""
        self.modify(field, block, value, -1)

class Instance:
    """Class representing an instance of a register file, abstracting access to
    its fields to bus read/write functions.

     - Accessing registers: use attribute access with the name patterns
       `R_<mnemonic>` or `r_<name>`. Reading such an attribute returns an
       object for which the values of the individual fields can be accessed
       using attribute access or indexation. Writes to such an attribute can be
       done using objects with attributes of the same name or a dictionary-like
       object with keys of the same name. If no data is available for some of
       the fields or their values are `None`, this class will attempt to write
       only those fields.

     - Accessing scalar fields: use attribute access with the name patterns
       `F_<reg-mnemonic>_<field-mnemonic>` or `f_<field-name>`. Reads return
       the unsigned integer representation of the field. Writes can be done
       using integers, booleans, or bit-strings of the right size.

     - Accessing array fields: either use attribute access with index embedded
       in the name using the name pattern `f_<field-name><index>`, or use
       `f_<field-name>` and index the result with Python-style indexation.

     - Accessing multi-block fields (such as AXI passthrough): use Python
       indexation to select the block index to access. If the multi-block field
       is also an array, the field index comes before the block index.

    Fields that can be indexed (either field index or block index) can also be
    iterated over to read all in sequence.

    You can also drop the `R_`, `r_`, `F_`, or `f_` prefixes if you like. But
    be aware that this can result in name conflicts. Fields take precedence in
    case of a register/field conflict, and prefixed names take precedence over
    non-prefixed names.

    All of the above attribute accesses can also done using indexation.

    Note that accessing individual fields is not always possible, even in read
    mode, since fields can be volatile. In write mode, fields may not be on
    byte strobe boundaries (or may ignore strobes), which may prevent
    individual writes of neighboring fields; this class will attempt to do a
    read-modify-write in this case, but this, too, is not always possible, for
    instance if the field cannot be read."""

    def __init__(self, regfile, read_fn=None, write_fn=None, lock=False, base=0):
        """Constructs a register file instance.

         - `regfile`: the description of the register file to access. This can
           be any of the following:
            - a completed `vhdmmio.core.regfile.RegisterFile` instance;
            - anything that can be passed to the static `load()` method of the
              above, such as a YAML/JSON filename, a file object, or a
              dictionary.

         - `read_fn`: should be a function of type `int -> int` that reads from
           the MMIO bus, where the argument is the byte address and the result
           is the bus word read from that address. If `None`, the register file
           is write-only.

         - `write_fn`: should be a function of type `int, int, [int] -> None`
           that writes to the MMIO bus, where the arguments are the address to
           write, the value to write to it, and (if specified), the byte strobe
           signals. If `None`, the register file is read-only.

         - `lock`: this specifies how to lock access to the register file when
           multiple accesses need to be performed. The following values can be
           used:
             - some kind of class that supports the context protocol
               (`__enter__()` and `__exit__()`): this context will be claimed
               whenever an access or set of accesses needs to be performed. Any
               lock class from Python's threading module will do, for instance.
             - `None`: accesses cannot be locked. Any attempt to do a
               multi-register access results in an error.
             - `False` (the default): all accesses to the register file are
               assumed to go through this class in this Python process. A
               `threading.RLock` is created automatically to still be
               Python-thread-safe.

         - `base`: an optional integer that is added to all addresses before
           they are passed to `read_fn()`/`write_fn()`.
        """
        super().__init__()

        self._regfile = regfile
        self._read_fn = read_fn
        self._write_fn = write_fn
        self._lock = lock
        self._base = int(base)

        # Desugar arguments.
        if not isinstance(self._regfile, RegisterFile):
            self._regfile = RegisterFile.load(self._regfile)
        if self._lock is False:
            self._lock = threading.RLock()

        # Construct a dictionary of the name patterns that can be used to
        # access the fields and registers of this register file. A name can map
        # to:
        #  - a `Register`: the entire register is to be accessed.
        #  - a `Register`: the entire register is to be accessed.
        names_pre = {}
        names_raw = {}
        def define(prefix, name, value):
            names_raw['%s' % name] = value
            names_pre['%s_%s' % (prefix, name)] = value
        for register in self._regfile.registers:
            define('r', register.meta.name, register)
            define('R', register.meta.mnemonic, register)
        for field_descriptor in self._regfile.field_descriptors:
            if field_descriptor.vector_count is not None:
                define('f', field_descriptor.meta.name, field_descriptor)
            for field in field_descriptor.fields:
                reg_mnem = field.register.meta.mnemonic
                mnem = field.meta.mnemonic
                define('f', field.meta.name, field)
                define('F', '%s_%s' % (reg_mnem, mnem), field)
        self._names = names_raw
        self._names.update(names_pre)

    @property
    def regfile(self):
        """Returns the associated `RegisterFile` object."""
        return self._regfile

    @property
    def bus_width(self):
        """Returns the width of the register file access bus in bits."""
        return self._regfile.bus_width

    @property
    def bus_size(self):
        """Returns the number of LSBs that the register file access bus ignores
        in addresses due to its width."""
        return 2 if self._regfile.bus_width == 32 else 3

    def read_raw(self, offset):
        """Raw read access to this register file, offset by its base
        address. Returns the value as an int. The lock is not claimed."""
        if self._read_fn is None:
            raise ValueError('this register file cannot be read')
        return self._read_fn(address + self._base)

    def write_raw(self, offset, data, strobe=-1):
        """Raw write access to this register file, offset by its base
        address. The lock is not claimed."""
        if self._write_fn is None:
            raise ValueError('this register file cannot be written')
        return self._write_fn(address + self._base, data, strobe)

    # Context protocol for locking:
    def __enter__(self):
        """Locks this register file for exclusive access."""
        if self._lock is None:
            raise ValueError('cannot lock this register file instance for exclusive access')
        self._lock.__enter__()
        return self

    def __exit__(self, *args):
        """Unlocks exclusive access to this register file."""
        self._lock.__exit__(*args)

    def _read_field(self, field, block=0):
        """Reads the given block of a field."""

    def _write_field(self, field, value, block=0):
        """Writes the given block of a field."""

    def _read_object(self, obj):
        """Reads a field or register."""
        if isinstance(obj, Register):
            # Whole-register read.
            return self._read_register(self, obj)

        if isinstance(obj, Field):
            # Single-field read.
            if obj.bitrange.size > self.bus_size:
                nblocks = 2**(obj.bitrange.size - self.bus_size)
                class MultiBlockField:
                    @staticmethod
                    def __getitem__(block):
                        return self._read_field(obj, block)
                    @staticmethod
                    def __setitem__(block, value):
                        self._write_field(obj, value, block)
                    def __iter__(self):
                        for i in range(len(self)):
                            yield self[i]
                    @staticmethod
                    def __len__():
                        return nblocks
                return MultiBlockField()
            return self._read_field(obj)

        if isinstance(obj, FieldDescriptor):
            # Return indexable object representing array field indexation.
            class IndexableField:
                @staticmethod
                def __getitem__(index):
                    return self._read_object(obj.fields[index])
                @staticmethod
                def __setitem__(index, value):
                    self._write_object(obj.fields[index], value)
                def __iter__(self):
                    for i in range(len(self)):
                        yield self[i]
                @staticmethod
                def __len__():
                    return obj.vector_count
            return IndexableField()

        raise NotImplementedError()

    def _write_object(self, obj, value):
        """Writes a field or register."""
        if isinstance(obj, Register):
            # Whole-register write.
            self._write_register(obj, value)
            return

        if isinstance(obj, Field):
            # Single-field read.
            if obj.bitrange.size > self.bus_size:
                nblocks = 2**(obj.bitrange.size - self.bus_size)
                self._write_field(obj, value, slice(nblocks))
                return
            self._write_field(obj, value)
            return

        if isinstance(obj, FieldDescriptor):
            # Return indexable object representing array field indexation.
            class IndexableField:
                @staticmethod
                def __getitem__(index):
                    return self._read_object(obj.fields[index])
                @staticmethod
                def __setitem__(index, value):
                    self._write_object(obj.fields[index], value)
                def __iter__(self):
                    for i in range(len(self)):
                        yield self[i]
                @staticmethod
                def __len__():
                    return obj.vector_count
            return IndexableField()

        raise NotImplementedError()

    # Mapping protocol for register/field access:
    def __getitem__(self, key):
        return self._read_object(self._names[key])

    def __setitem__(self, key, value):
        return self._write_object(self._names[key], value)

    def __iter__(self):
        return iter(self._names)

    def __len__(self):
        return len(self._names)

    def __contains__(self, key):
        return key in self._names

    # Attribute protocol for register/field access:
    def __getattr__(self, attribute):
        obj = self._names.get(attribute, None)
        if obj is None:
            raise AttributeError('%s attribute does not exist' % attribute)
        return self._read_object(obj)

    def __setattr__(self, attribute, value):
        obj = self._names.get(attribute, None)
        if obj is None:
            raise AttributeError('%s attribute does not exist' % attribute)
        return self._write_object(obj, value)
