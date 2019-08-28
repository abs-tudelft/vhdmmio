"""Field behaviors for counting events."""

import re
from ...configurable import derive, checked, ParseError
from .registry import behavior, behavior_doc
from .primitive import Primitive

behavior_doc('Fields for counting events:', 1)

@behavior(
    'counter', 'external event counter, reset explicitly by a write.', 2)
@derive(
    name='`counter` behavior',
    bus_read='enabled',
    after_bus_read='nothing',
    bus_write='subtract',
    after_bus_write='nothing',
    hw_read=('disabled', 'simple'),
    hw_write=('disabled', 'enabled', 'accumulate', 'subtract'),
    after_hw_write='nothing',
    ctrl_lock=False,
    ctrl_validate=False,
    ctrl_invalidate=False,
    ctrl_ready=False,
    ctrl_clear=[False],
    ctrl_reset=[False],
    ctrl_increment=[True],
    ctrl_decrement=[False],
    ctrl_bit_set=False,
    ctrl_bit_clear=False,
    ctrl_bit_toggle=False,
    drive_internal=None,
    full_internal=None,
    empty_internal=None,
    bit_overflow_internal=None,
    bit_underflow_internal=None,
    overrun_internal=None,
    underrun_internal=None,
    monitor_internal=None,
    monitor_mode='increment',
    reset=(False, True, int, 'generic'))
class Counter(Primitive):
    """Similar to `flag` fields, `counter`s are used to signal events from
    hardware to software. However, counters allow multiple events occurring
    between consecutive software read cycles to be registered by counting
    instead of bit-setting. Like `flag`, software should use fields of this
    type by reading the value and then writing the read value to it in order
    to avoid missing events; the write operation subtracts the written value
    from the internal register.

    When a counter overflows, it simply wraps back to zero. Similarly, if a
    counter is decremented below zero, it wraps to its maximum value.
    Optionally, `overflow-internal` and `underflow-internal` can be used to
    detect this condition, in conjuntion with an `internal-flag` field and/or
    an internal interrupt."""

@behavior(
    'volatile-counter', 'external event counter, reset implicitly by the '
    'read.', 2)
@derive(
    name='`volatile-counter` behavior',
    after_bus_read='clear',
    bus_write='disabled',
    underflow_internal=None)
class VolatileCounter(Counter):
    """This behavior is similar to `counter`, but the counter value is
    immediately cleared when the field is read. The field is therefore
    read-only, allowing write-only registers to reside at the same address
    The access procedure is also slightly faster, because no write action is
    required. However, the required read-volatility makes it incompatible
    with processors/caches that prefetch values; any infrastructure that
    may perform spurious reads may inadvertantly clear the counter."""

@behavior(
    'internal-counter', 'internal event counter, reset explicitly by a write.', 2)
@derive(
    name='`internal-counter` behavior',
    ctrl_increment=[False])
class InternalCounter(Counter):
    """This field behaves like `counter`, but instead of the counter being
    incremented by an external signal, it is incremented by an internal
    signal."""

    @checked
    def internal(self, value):
        """Configures the internal signal that is to be monitored. The value
        must be a string matching `[a-zA-Z][a-zA-Z0-9_]*`."""
        if not isinstance(value, str) or not re.fullmatch(r'[a-zA-Z][a-zA-Z0-9_]*', value):
            ParseError.invalid('', value, 'a string matching `[a-zA-Z][a-zA-Z0-9_]*`')
        self.monitor_internal = value
        return value

@behavior(
    'volatile-internal-counter', 'internal event counter, reset implicitly by the '
    'read.', 2)
@derive(
    name='`volatile-internal-counter` behavior',
    ctrl_increment=[False])
class VolatileInternalCounter(VolatileCounter):
    """This field behaves like `volatile-counter`, but instead of the counter
    being incremented by an external signal, it is incremented by an internal
    signal."""

    @checked
    def internal(self, value):
        """Configures the internal signal that is to be monitored. The value
        must be a string matching `[a-zA-Z][a-zA-Z0-9_]*`."""
        if not isinstance(value, str) or not re.fullmatch(r'[a-zA-Z][a-zA-Z0-9_]*', value):
            ParseError.invalid('', value, 'a string matching `[a-zA-Z][a-zA-Z0-9_]*`')
        self.monitor_internal = value
        return value
