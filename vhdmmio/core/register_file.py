"""Submodule for the root class for a complete register file."""

from .mixins import Named, Configured, Unique
from .resources import Resources
from .field_descriptor import FieldDescriptor
from .logical_register import construct_logical_register
from .interrupt import Interrupt, InterruptInfo
from .defer_tag import DeferTagInfo


class RegisterFile(Named, Configured, Unique):
    """Compiled representation of a register file."""

    def __init__(self, cfg, trusted):
        self._trusted = trusted
        super().__init__(cfg=cfg, metadata=cfg.metadata)
        with self.context:

            # Create the various resource managers.
            resources = Resources(self)

            # Parse the field descriptors.
            self._field_descriptors = tuple((
                FieldDescriptor(resources, self, field_descriptor_cfg)
                for field_descriptor_cfg in cfg.fields))

            # The `FieldDescriptor` constructor calls the `Field` constructor,
            # which in turn maps the field addresses to lists of `Field`s in
            # `resources.addresses`. We can now convert these lists to
            # `LogicalRegister`s, of which the constructor also constructs the
            # `Block`s.
            registers = []
            addresses = resources.addresses
            for address in addresses:

                # Construct the register(s) for this address.
                read_reg, write_reg = construct_logical_register(
                    resources, self,
                    addresses.read.pop(address, None),
                    addresses.write.pop(address, None))

                # Add the constructed registers to the list of all registers in
                # this register file.
                if read_reg is not None:
                    registers.append(read_reg)
                if write_reg is not None and write_reg is not read_reg:
                    registers.append(write_reg)

            # Convert the register list to a tuple to make it immutable.
            self._registers = tuple(registers)

            # Determine if the register file should be hardened against
            # privilege escalation.
            self._need_prot = any(map(lambda register: register.is_protected(), registers))
            self._harden = self._need_prot and not cfg.features.insecure

            # Parse the interrupts.
            self._interrupts = tuple((
                Interrupt(resources, self, interrupt_cfg)
                for interrupt_cfg in cfg.interrupts))

            # Parse the I/O configuration for internals.
            for internal_io_config in cfg.internal_io:
                resources.internals.add_io(internal_io_config)

            # Perform post-construction checks on the resource managers.
            resources.verify_and_freeze()
            self._resources = resources

            # Expose the requisite information about the used resources in an
            # immutable way.
            self._defer_tag_info = DeferTagInfo(
                resources.read_tags, resources.write_tags, cfg.features.max_outstanding)
            self._interrupt_info = InterruptInfo(
                resources.interrupts)
            self._internals = tuple(resources.internals)
            self._internal_ios = tuple(resources.internals.iter_internal_ios())

    @property
    def trusted(self):
        """Whether source of the configuration used to construct this register
        file is trusted. If not, custom fields are disabled, since their
        template code can execute arbitrary Python code."""
        return self._trusted

    @property
    def field_descriptors(self):
        """The field descriptors of this register file as a tuple."""
        return self._field_descriptors

    @property
    def registers(self):
        """The logical registers of this register file as a tuple."""
        return self._registers

    @property
    def interrupts(self):
        """The interrupts of this register file as a tuple."""
        return self._interrupts

    @property
    def internals(self):
        """The internal signals used in this register file as a tuple."""
        return self._internals

    @property
    def internal_ios(self):
        """The internal signal I/O ports for this register file as a tuple."""
        return self._internal_ios

    def doc_iter_blocks(self):
        """Iterates over the blocks in a natural order for documentation
        output. The elements are yielded as
        `(subaddresses, address_repr, read_block, write_block)` tuples, where
        `address_repr` is a human-readable string representation of the
        address, and `read_block`/`write_block` are `None` if the address range
        is write-only/read-only, and may be identical for read-write blocks."""
        return self._resources.addresses.doc_iter()

    def doc_represent_address(self, internal_address):
        """Formats documentation for the given internal address. Returns a
        tuple of the formatted address and a list of string representations of
        any additional match conditions."""
        return self._resources.addresses.doc_represent_address(internal_address)

    @property
    def address_info(self):
        """Information the concatenated internal address signals. See
        `address.AddressSignalMap`."""
        return self._resources.addresses.signals

    def iter_subaddresses(self):
        """Iterates over the subaddresses used in the register file."""
        return iter(self._resources.subaddresses)

    @property
    def defer_tag_info(self):
        """Information about the defer tags used by this register file. See
        `defer_tag.DeferTagInfo`."""
        return self._defer_tag_info

    @property
    def interrupt_info(self):
        """Information about the concatenated interrupt vector."""
        return self._interrupt_info

    @property
    def need_prot(self):
        """Whether any field within the register file is prot-sensitive."""
        return self._need_prot

    @property
    def harden(self):
        """Whether the register file should be hardened against privilege
        escalation. Note that this hardening is not at all sufficient on its
        own!"""
        return self._harden

    def get_max_logical_register_width(self, filt=None):
        """Returns the number of bits in the widest logical register satisfying
        the provided filter condition, if any."""
        registers = self.registers
        if not registers:
            return self.cfg.features.bus_width
        if filt is not None:
            registers = filter(filt, self.registers)
        max_blocks = max(map(lambda register: len(register.blocks), registers), default=1)
        return max_blocks * self.cfg.features.bus_width

    def get_max_logical_read_width(self):
        """Returns the number of bits in the widest readable logical
        register."""
        return self.get_max_logical_register_width(lambda register: register.can_read())

    def get_max_logical_write_width(self):
        """Returns the number of bits in the widest writable logical
        register."""
        return self.get_max_logical_register_width(lambda register: register.can_write())
