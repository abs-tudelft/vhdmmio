"""Module for `RegisterFile` object."""

import os
import json
import yaml
from .metadata import Metadata, ExpandedMetadata
from .field import FieldDescriptor
from .register import Register
from .interrupt import Interrupt
from ..vhdl.interface import InterfaceOptions

class RegisterFile:
    """Represents a register file."""

    def __init__(self, **kwargs):
        """Constructs a register file.

        The named arguments to this function match the toplevel dictionaries
        accepted in the YAML input format, except the dashes are replaced with
        underscores to make them proper Python identifiers.

        To load a register file from a YAML file or the associated dictionary,
        use the `load()` function. You can also `save()` back to an equivalent
        YAML file."""

        self.output_directory = None

        # Parse metadata.
        meta = kwargs.pop('meta', None)
        if meta is None:
            raise ValueError('missing meta key for register file')
        meta = meta.copy()
        self._meta = Metadata.from_dict(None, meta)
        for key in meta:
            raise ValueError('unexpected key in register file metadata: %s' % key)

        try:

            # Parse features subdict.
            features = kwargs.pop('features', {}).copy()

            # Parse bus width.
            self._bus_width = int(features.pop('bus-width', 32))
            if self._bus_width not in (32, 64):
                raise ValueError('bus-width must be 32 or 64')

            # Parse maximum outstanding request count.
            self._max_outstanding = int(features.pop('max-outstanding', 16))
            if self._max_outstanding < 2:
                raise ValueError('maximum number of outstanding requests must be at least 2')
            self._tag_depth_log2 = int.bit_length(self._max_outstanding) - 1
            if self._max_outstanding != 2**self._tag_depth_log2:
                raise ValueError('maximum number of outstanding requests must be a power of 2')

            # Parse security flag.
            self._insecure = bool(features.pop('insecure', False))

            # Parse address decoder optimization flag.
            self._optimize = bool(features.pop('optimize', False))

            # Check for unknown keys.
            for key in features:
                raise ValueError('unexpected key in register file features: %s' % key)

            # Parse interface options.
            iface_opts = kwargs.pop('interface', None)
            if iface_opts is None:
                iface_opts = {}
            self._iface_opts = InterfaceOptions.from_dict(iface_opts)

            # Read the interrupts.
            self._interrupts = tuple((
                Interrupt.from_dict(self, d) for d in kwargs.pop('interrupts', [])))

            # Give each interrupt an index.
            self._interrupt_count = 0
            for interrupt in self._interrupts:
                interrupt.index = self._interrupt_count
                self._interrupt_count += 1 if interrupt.width is None else interrupt.width

            # Read the fields.
            field_descriptors = []
            def merge_dict(dictionary, prototype):
                for key, proto_value in prototype.items():
                    if isinstance(proto_value, dict):
                        if isinstance(dictionary.get(key, None), dict):
                            merge_dict(dictionary[key], proto_value)
                            continue
                    dictionary[key] = proto_value
            def process_field(dictionary, prototype):
                subfields = dictionary.pop('subfields', None)
                merge_dict(dictionary, prototype)
                if subfields is None:
                    field_descriptors.append(FieldDescriptor.from_dict(self, dictionary))
                    return
                for subfield in subfields:
                    process_field(subfield, dictionary)
            for dictionary in kwargs.pop('fields', []):
                process_field(dictionary, {})
            self._field_descriptors = tuple(field_descriptors)

            # Connect interrupt control fields to interrupts.
            for field_descriptor in self._field_descriptors:
                if hasattr(field_descriptor.logic, 'irq_name'):
                    irq_name = field_descriptor.logic.irq_name
                    for interrupt in self._interrupts:
                        if interrupt.meta.name == irq_name:
                            field_descriptor.logic.interrupt = interrupt
                            break
                    else:
                        raise ValueError('could not find interrupt named "%s" for field %s' % (
                            irq_name, field_descriptor.meta.name))

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
                    register.assign_write_tag(write_tag_format.format(self._write_tag_count))
                    self._write_tag_count += 1

            # Determine whether any fields are sensitive to prot.
            self._secure = False
            for field_descriptor in self._field_descriptors:
                if field_descriptor.read_prot != '---':
                    self._secure = True
                    break
                if field_descriptor.write_prot != '---':
                    self._secure = True
                    break
            if self._insecure:
                self._secure = False

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

        # Write features.
        features = {}
        if self._bus_width != 32:
            features['bus-width'] = self._bus_width
        if self._max_outstanding != 16:
            features['max-outstanding'] = self._max_outstanding
        if self._insecure:
            features['insecure'] = True
        if self._optimize:
            features['optimize'] = True
        if features:
            dictionary['features'] = features

        # Write interface options.
        iface = self._iface_opts.to_dict()
        if iface:
            dictionary['interface'] = iface

        # Write interrupts.
        dictionary['interrupts'] = []
        for interrupt in self._interrupts:
            dictionary['interrupts'].append(interrupt.to_dict())

        # Write fields.
        dictionary['fields'] = []
        for field in self._field_descriptors:
            dictionary['fields'].append(field.to_dict())

        return dictionary

    @classmethod
    def load(cls, obj):
        """Creates a `RegisterFile` object from one of the following:

         - A YAML or JSON filename (if the file extension is `.json` JSON is
           used, otherwise YAML is assumed);
         - A file-like object reading a YAML file;
         - A dictionary representation of the JSON or YAML file.

        Returns the constructed `RegisterFile` if the input is valid."""

        loader = yaml.safe_load if hasattr(yaml, 'safe_load') else yaml.load

        if isinstance(obj, dict):
            return cls.from_dict(obj)

        if isinstance(obj, str):
            if obj.lower().endswith('.json'):
                loader = json.loads
            with open(obj, 'r') as fil:
                regfile = cls.from_dict(loader(fil.read()))
            regfile.output_directory = os.path.dirname(obj)
            return regfile

        if hasattr(obj, 'read'):
            return cls.from_dict(loader(obj.read()))

        raise TypeError('unsupported input for load() API')

    def save(self, obj=None):
        """Serializes a `RegisterFile` in one of the following ways:

         - If `obj` is a filename string, write the YAML (default) or JSON
           (if the name ends in `.json`) representation to it;
         - If `obj` is file-like, write the YAML representation into it;
         - If `obj` is `None` or not provided, return the dictionary
           representation."""

        data = self.to_dict(None)

        if obj is None:
            return data

        if isinstance(obj, str) and obj.lower().endswith('.json'):
            data = json.dumps(data, sort_keys=True, indent=4)
        else:
            data = yaml.dump(data, default_flow_style=False)

        if isinstance(obj, str):
            with open(obj, 'w') as fil:
                fil.write(data)
            return None

        if hasattr(obj, 'write'):
            obj.write(data)
            return None

        raise TypeError('unsupported input for save() API')

    @property
    def meta(self):
        """Metadata for this register file."""
        return self._meta[None]

    @property
    def bus_width(self):
        """Returns the bus width for this register file."""
        return self._bus_width

    @property
    def iface_opts(self):
        """Returns an `InterfaceOptions` object, carrying the default options
        for generating the VHDL interface."""
        return self._iface_opts

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

    def get_interrupt_strobe_mask(self):
        """Returns the bit vector used to mask the interrupt flags every cycle.
        0 means an interrupt is level-sensitive, 1 means an interrupt is
        strobe-sensitive."""
        vector = ''
        for interrupt in reversed(self.interrupts):
            width = interrupt.width
            if width is None:
                width = 1
            if interrupt.can_clear:
                vector += '1' * width
            else:
                vector += '0' * width
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
        n_blocks = max((
            r.block_count
            for r in self._registers
            if r.read_caps is not None
            ), default=1)
        return self._bus_width * n_blocks

    def get_max_logical_write_width(self):
        """Returns the width in bits of the largest writable register."""
        n_blocks = max((
            r.block_count
            for r in self._registers
            if r.write_caps is not None
            ), default=1)
        return self._bus_width * n_blocks

    @property
    def secure(self):
        """Indicates whether this register file implements security features
        based on the AXI4-lite `prot` field."""
        return self._secure

    @property
    def optimize(self):
        """Indicates whether the address decoder can be optimized."""
        return self._optimize

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
