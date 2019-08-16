"""Submodule for interrupt field behavior."""

from .base import Behavior, behavior, BusAccessNoOpMethod, BusAccessBehavior, BusBehavior
from ...config.behavior import Interrupt

@behavior(Interrupt)
class InterruptBehavior(Behavior):
    """Behavior class for interrupt fields."""

    def __init__(self, resources, field, behavior_cfg, read_allow_cfg, write_allow_cfg):

        # Check the shape of the field.
        if field.bitrange.is_vector():
            raise ValueError('interrupt fields cannot be vectors, use repetition instead')

        # Check the behavior configuration.
        if behavior_cfg.bus_read == 'disabled' and behavior_cfg.bus_write == 'disabled':
            raise ValueError('bus cannot access the field; specify a read or write operation')

        if behavior_cfg.mode in ('raw', 'masked') and behavior_cfg.bus_write != 'disabled':
            raise ValueError('%s interrupt fields cannot be written' % behavior_cfg.mode)

        if behavior_cfg.bus_read == 'clear' and behavior_cfg.mode != 'flag':
            raise ValueError('only flag interrupt fields support clear-on-read')

        # Construct the bus read behavior.
        if behavior_cfg.bus_read == 'disabled':
            can_read_for_rmw = False
            read_behavior = None
        elif behavior_cfg.bus_read == 'clear':
            can_read_for_rmw = False
            read_behavior = BusAccessBehavior(
                read_allow_cfg,
                volatile=True,
                no_op_method=BusAccessNoOpMethod.NEVER)
        else:
            can_read_for_rmw = True
            read_behavior = BusAccessBehavior(
                read_allow_cfg,
                no_op_method=BusAccessNoOpMethod.ALWAYS)

        # Construct the bus write behavior.
        if behavior_cfg.bus_write == 'disabled':
            write_behavior = None
        elif behavior_cfg.bus_write in ('set', 'clear'):
            write_behavior = BusAccessBehavior(
                write_allow_cfg,
                no_op_method=BusAccessNoOpMethod.WRITE_ZERO)
        else:
            write_behavior = BusAccessBehavior(
                write_allow_cfg,
                no_op_method=BusAccessNoOpMethod.WRITE_CURRENT_OR_MASK)

        super().__init__(
            field, behavior_cfg,
            BusBehavior(read_behavior, write_behavior, can_read_for_rmw))

        self._interrupt = None

        # Register this field with the interrupt resource manager.
        resources.interrupts.register_field(field)

    def attach_interrupt(self, interrupt):
        """Attaches the `Interrupt` object that this field is connected to.
        This can only be called once; it should be called during construction
        of the register file."""
        with self.field.context:
            if self._interrupt is not None:
                raise ValueError('interrupt already attached')
            if self.field.bitrange.shape != interrupt.shape:
                raise ValueError('mismatch between field and interrupt repetition')
            self._interrupt = interrupt

    @property
    def interrupt(self):
        """The `Interrupt` object connected to this field."""
        if self._interrupt is None:
            raise ValueError('interrupt not yet attached')
        return self._interrupt
