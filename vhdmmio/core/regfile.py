"""Module for `RegisterFile` object."""

from .metadata import Metadata, ExpandedMetadata
from .field import FieldDescriptor
from .register import Register
from .interrupt import Interrupt

class RegisterFile:
    """Represents a register file."""

    def __init__(self, **kwargs):
        """Constructs a register file from its YAML description."""

        # Parse metadata.
        meta = kwargs.pop('meta', None)
        if meta is None:
            raise ValueError('missing meta key for register file')
        meta = meta.copy()
        self._meta = Metadata.from_dict(None, meta)
        for key in meta:
            raise ValueError('unexpected key in register file metadata: %s' % key)

        try:

            # Parse bus width.
            self._bus_width = int(kwargs.pop('bus_width', 32))
            if self._bus_width not in (32, 64):
                raise ValueError('bus-width must be 32 or 64')

            # Parse maximum outstanding request count.
            max_outstanding = int(kwargs.pop('max_outstanding', 16))
            if max_outstanding < 2:
                raise ValueError('maximum number of outstanding requests must be at least 2')
            self._tag_depth_log2 = int.bit_length(max_outstanding) - 1
            if max_outstanding != 2**self._tag_depth_log2:
                raise ValueError('maximum number of outstanding requests must be a power of 2')

            # Read the interrupts.
            self._interrupts = tuple((
                Interrupt.from_dict(self, d) for d in kwargs.pop('interrupts', [])))

            # Give each interrupt an index.
            self._interrupt_count = 0
            for interrupt in self._interrupts:
                interrupt.index = self._interrupt_count
                self._interrupt_count += 1 if interrupt.width is None else interrupt.width

            # Read the fields.
            self._field_descriptors = tuple((
                FieldDescriptor.from_dict(self, d) for d in kwargs.pop('fields', [])))

            # Construct registers from the fields.
            reg_map = {}
            for field_descriptor in self._field_descriptors:
                for field in field_descriptor.fields:
                    addr = field.bitrange.address
                    if addr not in reg_map:
                        reg_map[addr] = []
                    reg_map[addr].append(field)
            self._registers = tuple((Register(*fields) for _, fields in sorted(reg_map.items())))

            # Assign read and write tags to registers that can defer accesses
            # (= multiple outstanding requests).
            self._read_tag_count = 0
            self._write_tag_count = 0
            for register in self._registers:
                if register.read_caps is not None and register.read_caps.can_defer:
                    self._read_tag_count += 1
                if register.write_caps is not None and register.write_caps.can_defer:
                    self._write_tag_count += 1
            read_tag_format = '"{:0%db}"' % self.read_tag_width
            write_tag_format = '"{:0%db}"' % self.write_tag_width
            self._read_tag_count = 0
            self._write_tag_count = 0
            for register in self._registers:
                if register.read_caps is not None and register.read_caps.can_defer:
                    register.assign_read_tag(read_tag_format.format(self._read_tag_count))
                    self._read_tag_count += 1
                if register.write_caps is not None and register.write_caps.can_defer:
                    register.assign_read_tag(write_tag_format.format(self._write_tag_count))
                    self._write_tag_count += 1

            # Check for overlapping registers. Note that this assumes that the
            # registers are ordered by address, which we do in the one-liner above.
            min_read = 0
            prev_read = None
            min_write = 0
            prev_write = None
            for register in self._registers:
                if register.read_caps is not None:
                    if register.address < min_read:
                        raise ValueError('registers %s and %s overlap in read mode'
                                         % (prev_read, register))
                    min_read = register.address_high + 1
                    prev_read = register
                if register.write_caps is not None:
                    if register.address < min_write:
                        raise ValueError('registers %s and %s overlap in write mode'
                                         % (prev_write, register))
                    min_write = register.address_high + 1
                    prev_write = register

            # Check for naming conflicts.
            ExpandedMetadata.check_siblings((
                irq.meta
                for irq in self._interrupts))
            ExpandedMetadata.check_siblings((
                reg.meta
                for reg in self._registers))
            ExpandedMetadata.check_cousins((
                field.meta
                for reg in self._registers
                for field in reg.fields))

            # Check for unknown keys.
            for key in kwargs:
                raise ValueError('unexpected key in field description: %s' % key)

        except (ValueError, TypeError) as exc:
            raise type(exc)('while parsing register file %s: %s' % (self._meta.name, exc))

    @classmethod
    def from_dict(cls, dictionary):
        """Constructs a register file object from a dictionary."""
        dictionary = dictionary.copy()
        for key in list(dictionary.keys()):
            if '-' in key:
                dictionary[key.replace('-', '_')] = dictionary.pop(key)
        return cls(**dictionary)

    def to_dict(self, dictionary=None):
        """Returns a dictionary representation of this register file."""
        if dictionary is None:
            dictionary = {}

        # Write metadata.
        dictionary['meta'] = {}
        self._meta.to_dict(dictionary['meta'])

        # Write interrupts.
        dictionary['interrupts'] = []
        for interrupt in self._interrupts:
            dictionary['interrupts'].append(interrupt.to_dict())

        # Write fields.
        dictionary['fields'] = []
        for field in self._field_descriptors:
            dictionary['fields'].append(field.to_dict())

        return dictionary

    @property
    def meta(self):
        """Metadata for this register file."""
        return self._meta[None]

    @property
    def bus_width(self):
        """Returns the bus width for this register file."""
        return self._bus_width

    @property
    def interrupts(self):
        """Returns the collection of interrupts that are part of this register
        file."""
        return self._interrupts

    @property
    def interrupt_count(self):
        """Returns the number of interrupts accepted by this register file."""
        return self._interrupt_count

    def get_interrupt_unmask_reset(self):
        """Returns the bit vector used to initialize the interrupt mask
        register."""
        vector = ''
        for interrupt in reversed(self.interrupts):
            width = interrupt.width
            if width is None:
                width = 1
            if interrupt.can_unmask:
                vector += '0' * width
            else:
                vector += '1' * width
        return vector

    def get_interrupt_enable_reset(self):
        """Returns the bit vector used to initialize the interrupt enable
        register."""
        vector = ''
        for interrupt in reversed(self.interrupts):
            width = interrupt.width
            if width is None:
                width = 1
            if interrupt.can_enable:
                vector += '0' * width
            else:
                vector += '1' * width
        return vector

    @property
    def read_tag_count(self):
        """Returns the number of read deferral tags used by this register
        file."""
        return self._read_tag_count

    @property
    def read_tag_width(self):
        """Returns the width of the `std_logic_vector` used to represent the
        read tags."""
        return max(1, int.bit_length(self._read_tag_count - 1))

    @property
    def write_tag_count(self):
        """Returns the number of write deferral tags used by this register
        file."""
        return self._write_tag_count

    @property
    def write_tag_width(self):
        """Returns the width of the `std_logic_vector` used to represent the
        write tags."""
        return max(1, int.bit_length(self._write_tag_count - 1))

    @property
    def tag_depth_log2(self):
        """Returns the number of bits used to represent the addresses of the
        deferral tag FIFOs."""
        return self._tag_depth_log2

    @property
    def tag_depth(self):
        """Returns the maximum number of in the deferral tag FIFOs. This is
        equivalent to the maximum number of outstanding requests for either
        operation."""
        return 2**self._tag_depth_log2

    def get_max_logical_read_width(self):
        """Returns the width in bits of the largest readable register."""
        n_blocks = max((r.block_count for r in self._registers if r.read_caps is not None))
        return self._bus_width * n_blocks

    def get_max_logical_write_width(self):
        """Returns the width in bits of the largest writable register."""
        n_blocks = max((r.block_count for r in self._registers if r.write_caps is not None))
        return self._bus_width * n_blocks

    @property
    def field_descriptors(self):
        """Returns the collection of field descriptors that are part of this
        register file."""
        return self._field_descriptors

    @property
    def registers(self):
        """Returns the collection of registers that are part of this register
        file."""
        return self._registers

    def __str__(self):
        return self.meta.name
