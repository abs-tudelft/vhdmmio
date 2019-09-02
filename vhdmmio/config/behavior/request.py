"""Flag-like fields for signalling requests from software to hardware."""

import re
from ...configurable import derive, checked, ParseError
from .registry import behavior, behavior_doc
from .primitive import Primitive, BasePrimitive

behavior_doc('Flag-like fields for signalling requests from software to hardware:', 1)

@behavior(
    'strobe', 'one flag per bit, strobed by an MMIO write to signal some '
    'request to hardware.', 2)
@derive(
    name='`strobe` behavior',
    bus_read='disabled',
    after_bus_read='nothing',
    bus_write='enabled',
    after_bus_write='invalidate',
    hw_read='simple',
    hw_write='disabled',
    after_hw_write='nothing',
    ctrl_lock=False,
    ctrl_validate=False,
    ctrl_invalidate=False,
    ctrl_ready=False,
    ctrl_clear=False,
    ctrl_reset=False,
    ctrl_increment=False,
    ctrl_decrement=False,
    ctrl_bit_set=False,
    ctrl_bit_clear=False,
    ctrl_bit_toggle=False,
    reset=0)
class Strobe(BasePrimitive):
    """This behavior may be used to signal a request to hardware, for hardware
    that can always handle the request immediately. When a 1 is written to a
    bit in this register, the respective output bit is strobed high for one
    cycle. Zero writes are ignored."""

@behavior(
    'internal-strobe', 'one flag per bit, strobed by an MMIO write to signal '
    'some request to another `vhdmmio` construct.', 2)
@derive(
    name='`internal-strobe` behavior',
    bus_read='disabled',
    after_bus_read='nothing',
    bus_write='enabled',
    after_bus_write='invalidate',
    hw_read='disabled',
    hw_write='disabled',
    after_hw_write='nothing',
    ctrl_lock=False,
    ctrl_validate=False,
    ctrl_invalidate=False,
    ctrl_ready=False,
    ctrl_clear=False,
    ctrl_reset=False,
    ctrl_increment=False,
    ctrl_decrement=False,
    ctrl_bit_set=False,
    ctrl_bit_clear=False,
    ctrl_bit_toggle=False,
    reset=0)
class InternalStrobe(BasePrimitive):
    """This behavior may be used to signal a request to another `vhdmmio`
    entity, such as a counter field. When a 1 is written to a bit in this
    register, the respective bit in the internal signal is strobed high for one
    cycle. Zero writes are ignored."""

    @checked
    def internal(self, value):
        """Configures the internal signal that is to be driven. The value
        must be a string matching `[a-zA-Z][a-zA-Z0-9_]*`."""
        if not isinstance(value, str) or not re.fullmatch(r'[a-zA-Z][a-zA-Z0-9_]*', value):
            ParseError.invalid('', value, 'a string matching `[a-zA-Z][a-zA-Z0-9_]*`')
        self.drive_internal = value
        return value

@behavior(
    'request', 'like `strobe`, but the request flags stay high until '
    'acknowledged by hardware.', 2)
@derive(
    name='`request` behavior',
    bus_read=('enabled', 'error', 'disabled'),
    after_bus_read='nothing',
    bus_write='bit-set',
    after_bus_write='nothing',
    hw_read='simple',
    hw_write='disabled',
    after_hw_write='nothing',
    ctrl_lock=False,
    ctrl_validate=False,
    ctrl_invalidate=False,
    ctrl_ready=False,
    ctrl_clear=[False],
    ctrl_reset=[False],
    ctrl_increment=False,
    ctrl_decrement=False,
    ctrl_bit_set=False,
    ctrl_bit_clear=[True],
    ctrl_bit_toggle=False,
    drive_internal=None,
    full_internal=None,
    empty_internal=None,
    overflow_internal=None,
    underflow_internal=None,
    bit_overflow_internal=[None],
    bit_underflow_internal=[None],
    overrun_internal=None,
    underrun_internal=None,
    monitor_internal=None,
    monitor_mode='status',
    reset=(False, True, int, 'generic'))
class Request(Primitive):
    """This behavior can be seen as both the inverse of a `flag` and as an
    extension of `strobe`: the bits in the field are set by software writing
    a one to them, and cleared when acknowledged by hardware. They can be used
    for requests that cannot be handled immediately. By default, software can
    use an MMIO read to determine whether a command has been acknowledged yet,
    but this can be disabled to make the field write-only."""

@behavior(
    'multi-request', 'allows multiple software-to-hardware requests to be '
    'queued up atomically by counting.', 2)
@derive(
    name='`multi-request` behavior',
    bus_read=('enabled', 'error', 'disabled'),
    after_bus_read='nothing',
    bus_write='accumulate',
    after_bus_write='nothing',
    hw_read='simple',
    hw_write=('disabled', 'subtract'),
    after_hw_write='nothing',
    ctrl_lock=False,
    ctrl_validate=False,
    ctrl_invalidate=False,
    ctrl_ready=False,
    ctrl_clear=[False],
    ctrl_reset=[False],
    ctrl_increment=False,
    ctrl_decrement=[True],
    ctrl_bit_set=False,
    ctrl_bit_clear=False,
    ctrl_bit_toggle=False,
    drive_internal=None,
    full_internal=None,
    empty_internal=None,
    overflow_internal=[None],
    underflow_internal=[None],
    bit_overflow_internal=None,
    bit_underflow_internal=None,
    overrun_internal=None,
    underrun_internal=None,
    monitor_internal=None,
    monitor_mode='status',
    reset=(False, True, int, 'generic'))
class MultiRequest(Primitive):
    """`multi-request` fields accumulate anything written to them, and by
    default allow hardware to decrement them. This may be used to request
    a certain number of things with a single, atomic MMIO write."""
