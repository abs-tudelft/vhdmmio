"""Submodule for AXI behavior."""

from .base import Behavior, behavior, BusAccessNoOpMethod, BusAccessBehavior, BusBehavior
from ...config.behavior import Axi

@behavior(Axi)
class AxiBehavior(Behavior):
    """Behavior class for AXI fields."""

    def __init__(self, resources, field_descriptor,
                 behavior_cfg, read_allow_cfg, write_allow_cfg):

        # Figure out the bus width.
        bus_width = field_descriptor.base_bitrange.width
        if bus_width not in [32, 64]:
            raise ValueError('AXI fields must be 32 or 64 bits wide')

        # Figure out the slice of the bus address that is controlled by the
        # subaddress.
        sub_low = {32: 2, 64: 3}[bus_width]
        sub_high = sub_low + field_descriptor.subaddress.width - 1
        if sub_high > 31:
            raise ValueError(
                'subaddress is too wide for %d-bit word address'
                % (32 - sub_low))
        self._subaddress_range = '%s downto %d' % (sub_high, sub_low)

        # Connect the internal signal for the interrupt.
        self._interrupt_internal = None
        if behavior_cfg.interrupt_internal is not None:
            self._interrupt_internal = resources.internals.drive(
                field_descriptor,
                behavior_cfg.interrupt_internal,
                field_descriptor.shape)

        # Decode the bus access behavior.
        if behavior_cfg.mode in ['read-only', 'read-write']:
            read_behavior = BusAccessBehavior(
                read_allow_cfg,
                blocking=True, volatile=True, deferring=True,
                no_op_method=BusAccessNoOpMethod.NEVER)
        else:
            read_behavior = None

        if behavior_cfg.mode in ['write-only', 'read-write']:
            write_behavior = BusAccessBehavior(
                write_allow_cfg,
                blocking=True, volatile=True, deferring=True,
                no_op_method=BusAccessNoOpMethod.NEVER)
        else:
            write_behavior = None

        bus_behavior = BusBehavior(
            read=read_behavior, write=write_behavior,
            can_read_for_rmw=False)

        super().__init__(field_descriptor, behavior_cfg, bus_behavior)

    @property
    def interrupt_internal(self):
        """The internal signal used for the interrupt signal that `vhdmmio`
        passes along with AXI4L busses, or `None` if this signal is not
        used."""
        return self._interrupt_internal

    @property
    def subaddress_range(self):
        """The slice of the child bus address in VHDL range notation that the
        subaddress maps to."""
        return self._subaddress_range

    @property
    def doc_reset(self):
        """The reset value as printed in the documentation as an integer, or
        `None` if the field is driven by a signal and thus does not have a
        register to reset."""
        return None
