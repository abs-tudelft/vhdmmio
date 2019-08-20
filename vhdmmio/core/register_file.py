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
            resources = Resources()

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
                    addresses.read.get(address, None),
                    addresses.write.get(address, None))

                # Replace the field lists with the constructed register
                # objects in the address managers.
                if read_reg is not None:
                    addresses.read[address] = read_reg
                elif address in addresses.read:
                    del addresses.read[address]

                if write_reg is not None:
                    addresses.write[address] = write_reg
                elif address in addresses.write:
                    del addresses.write[address]

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
            self._harden = (
                any(map(lambda register: register.is_protected(), registers))
                and not cfg.features.insecure)

            # Parse the interrupts.
            self._interrupts = tuple((
                Interrupt(resources, self, interrupt_cfg)
                for interrupt_cfg in cfg.interrupts))

            # Perform post-construction checks on the resource managers.
            resources.verify()
            self._resources = resources

            # Expose the requisite information about the used resources in an
            # immutable way.
            self._defer_tag_info = DeferTagInfo(
                resources.read_tags, resources.write_tags)
            self._interrupt_info = InterruptInfo(
                resources.interrupts)

    @property
    def trusted(self):
        """Whether source of the configuration used to construct this register
        file is trusted. If not, custom fields are disabled, since their
        template code can execute arbitrary Python code."""
        return self._trusted

    @property
    def field_descriptors(self):
        """Returns the field descriptors of this register file as a tuple."""
        return self._field_descriptors

    @property
    def registers(self):
        """Returns the logical registers of this register file as a tuple."""
        return self._registers

    @property
    def interrupts(self):
        """Returns the interrupts of this register file as a tuple."""
        return self._interrupts

    def doc_iter_registers(self):
        """Iterates over the registers in a natural order for documentation
        output. The elements are yielded as
        `(subaddresses, address_repr, read_ob, write_ob)` tuples, where
        `address_repr` is a human-readable string representation of the
        address, and `read_ob`/`write_ob` are `None` if the address range is
        write-only/read-only."""
        return self._resources.addresses.doc_iter()

    def doc_represent_address(self, internal_address):
        """Formats documentation for the given internal address. Returns a
        tuple of the formatted address and a list of string representations of
        any additional match conditions."""
        return self._resources.addresses.doc_represent_address(internal_address)

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
    def harden(self):
        """Whether the register file should be hardened against privilege
        escalation. Note that this hardening is not at all sufficient on its
        own!"""
        return self._harden

    def get_max_logical_register_width(self, filt=None):
        """Returns the number of bits in the widest logical register satisfying
        the provided filter condition, if any."""
        registers = self.registers
        if filt is not None:
            registers = filter(filt, self.registers)
        max_blocks = max(map(lambda register: len(register.blocks), registers))
        return max_blocks * self.cfg.features.bus_width

    def get_max_logical_read_width(self):
        """Returns the number of bits in the widest readable logical
        register."""
        return self.get_max_logical_register_width(lambda register: register.can_read())

    def get_max_logical_write_width(self):
        """Returns the number of bits in the widest writable logical
        register."""
        return self.get_max_logical_register_width(lambda register: register.can_write())
