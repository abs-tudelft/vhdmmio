"""Submodule for the root class for a complete register file."""

from .mixins import Named, Configured, Unique
from .resources import Resources
from .field_descriptor import FieldDescriptor
from .logical_register import construct_logical_register
from .interrupt import Interrupt

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

            # Parse the interrupts.
            self._interrupts = tuple((
                Interrupt(resources, self, interrupt_cfg)
                for interrupt_cfg in cfg.interrupts))

            # Perform post-construction checks on the resource managers.
            resources.verify()

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
