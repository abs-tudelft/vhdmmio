"""Flag-like field behaviors for signalling events from hardware to
software."""

import re
from ...configurable import derive, checked, ParseError
from .registry import behavior, behavior_doc
from .primitive import Primitive

behavior_doc('Flag-like fields for signalling events from hardware to software:', 1)

@behavior(
    'flag', 'one flag per bit, set by hardware and explicitly cleared by '
    'an MMIO write.', 2)
@derive(
    name='`flag` behavior',
    bus_read='enabled',
    after_bus_read='nothing',
    bus_write='bit-clear',
    after_bus_write='nothing',
    hw_read=('disabled', 'simple'),
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
    ctrl_bit_set=True,
    ctrl_bit_clear=False,
    ctrl_bit_toggle=False,
    drive_internal=None,
    full_internal=None,
    empty_internal=None,
    overflow_internal=None,
    underflow_internal=None,
    overrun_internal=None,
    underrun_internal=None,
    monitor_internal=None,
    monitor_mode='status',
    reset=(False, True, int, 'generic'))
class Flag(Primitive):
    """Fields with `flag' behavior behave like most edge/event-sensitive
    interrupt flags in commercial peripherals work: occurance of the event
    sets the flag bit, and writing a one to the bit through MMIO clears it
    again.

    Usually many of these flags are combined into a single register. Canonical
    usage by software is then to read the register to determine which events
    have occurred, write the read value back to the register, and then handle
    the events. If a new event occurs between the read and write, its flag
    will not be cleared, because a zero will be written to it by the write
    action. This event will then be handled the next time the software reads
    the flag register.

    It normally isn't possible to detect how many events have occurred for a
    single flag, just that there was at least one occurrance since the last
    read of the flag. If this information is necessary, the `counter` behavior
    can be used instead. If only the knowledge that an overflow occurred is
    needed, `bit-overflow-internal` can be used to drive an `internal-flag`
    field and/or an internal interrupt."""

@behavior(
    'volatile-flag', 'like `flag`, but implicitly cleared on read.', 2)
@derive(
    name='`volatile-flag` behavior',
    after_bus_read='clear',
    bus_write='disabled',
    bit_underflow_internal=None)
class VolatileFlag(Flag):
    """This behavior is similar to `flag`, but the flags are immediately
    cleared when the field is read. The field is therefore read-only, allowing
    write-only registers to reside at the same address. The access procedure
    is also slightly faster, because no write action is required. However, the
    required read-volatility makes it incompatible with processors/caches that
    prefetch values; any infrastructure that may perform spurious reads may
    inadvertantly clear the flags."""

@behavior(
    'internal-flag', 'like `flag`, but set by an internal signal.', 2)
@derive(
    name='`internal-flag` behavior',
    ctrl_bit_set=False,
    monitor_mode='bit-set')
class InternalFlag(Flag):
    """`internal-flag` fields behave like `flag` fields, but instead of the
    flags being set by an external signal, it is set by an internal signal.
    This may for instance be used in conjunction with the overrun output of an
    MMIO to stream field."""

    @checked
    def internal(self, value):
        """Configures the internal signal that is to be monitored. The value
        must be a string matching `[a-zA-Z][a-zA-Z0-9_]*`."""
        if not isinstance(value, str) or not re.fullmatch(r'[a-zA-Z][a-zA-Z0-9_]*', value):
            ParseError.invalid('', value, 'a string matching `[a-zA-Z][a-zA-Z0-9_]*`')
        self.monitor_internal = value
        return value

@behavior(
    'volatile-internal-flag', 'combination of `volatile-flag` and '
    '`internal-flag`.', 2)
@derive(
    name='`volatile-internal-flag` behavior',
    ctrl_bit_set=False,
    monitor_mode='bit-set')
class VolatileInternalFlag(VolatileFlag):
    """`volatile-internal-flag` fields behave like `volatile-flag` fields, but
    instead of the flags being set by an external signal, it is set by an
    internal signal. This may for instance be used in conjunction with the
    overrun output of an MMIO to stream field."""

    @checked
    def internal(self, value):
        """Configures the internal signal that is to be monitored. The value
        must be a string matching `[a-zA-Z][a-zA-Z0-9_]*`."""
        if not isinstance(value, str) or not re.fullmatch(r'[a-zA-Z][a-zA-Z0-9_]*', value):
            ParseError.invalid('', value, 'a string matching `[a-zA-Z][a-zA-Z0-9_]*`')
        self.monitor_internal = value
        return value
