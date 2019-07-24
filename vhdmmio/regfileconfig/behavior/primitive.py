"""Submodule for `Primitive` configurable."""

import re
from ...config import configurable, Configurable, flag, choice, checked, derive, Unset
from .registry import behavior, behavior_doc

@behavior(
    'primitive', 'base class for regular field behavior. Normally not used '
    'directly; it\'s easier to use one of its specializations:')
@configurable(name='`primitive` behavior', )
class Primitive(Configurable):
    """This is the base class for regular field behavior. It can be used for
    everything from simple status/control fields to stream interfaces and
    performance counters. Most behaviors simply derive from this by overriding
    some parameters and changing defaults for others.

    A primitive field has up to two internal registers associated with it. One
    contains data, and is thus as wide as the field is; the other is a single
    bit representing whether the data register is valid. How these registers
    are initialized and used (if at all) depends entirely on the
    configuration."""
    #pylint: disable=E0211,E0213

    @choice
    def bus_read():
        """Configures what happens when a bus read occurs."""
        yield 'disabled', 'read access is disabled.'
        yield 'error', 'reads always return a slave error.'
        yield 'enabled', 'normal read access to field, ignoring valid bit.'
        yield 'valid-wait', 'as above, but blocks until field is valid.'
        yield 'valid-only', 'as above, but fails when field is not valid.'

    @choice
    def after_bus_read():
        """Configures what happens after a bus read."""
        yield 'nothing', 'no extra operation after read.'
        yield 'invalidate', 'field is invalidated and cleared after read.'
        yield 'clear', 'field is cleared after read, valid untouched.'
        yield 'increment', 'Register is incremented after read, valid untouched.'
        yield 'decrement', 'Register is decremented after read, valid untouched.'

    @choice
    def bus_write():
        """Configures what happens when a bus write occurs."""
        yield 'disabled', 'Write access is disabled.'
        yield 'error', 'Writes always return a slave error.'
        yield 'enabled', 'Normal write access to register. Masked bits are written 0.'
        yield 'invalid', 'As above, but ignores the write when the register is valid.'
        yield 'invalid-wait', 'As above, but blocks until register is invalid.'
        yield 'invalid-only', 'As above, but fails when register is already valid.'
        yield 'masked', 'Write access respects strobe bits. Precludes after-bus-write.'
        yield 'accumulate', 'Write data is added to the register.'
        yield 'subtract', 'Write data is subtracted from the register.'
        yield 'bit-set', 'Bits that are written 1 are set in the register.'
        yield 'bit-clear', 'Bits that are written 1 are cleared in the register.'
        yield 'bit-toggle', 'Bits that are written 1 are toggled in the register.'

    @choice
    def after_bus_write():
        """Configures what happens after a bus write."""
        yield 'nothing', 'no extra operation after write.'
        yield 'validate', 'register is validated after write.'
        yield 'invalidate', 'as above, but invalidated again one cycle later.'

    @choice
    def hw_read():
        """Configure the existence and behavior of the hardware read port."""
        yield 'disabled', 'no read port is generated.'
        yield 'simple', 'only a simple data port is generated (no record).'
        yield 'enabled', 'a record of the data and valid bit is generated.'
        yield 'handshake', 'a stream-to-mmio ready signal is generated.'

    @choice
    def hw_write():
        """Configure the existence and behavior of the hardware write port."""
        yield 'disabled', 'no write port is generated.'
        yield 'status', 'the register is constantly driven by a port and is always valid.'
        yield 'enabled', 'a record consisting of a write enable flag and data is generated.'
        yield 'stream', 'like enabled, but the write only occurs when the register is invalid.'
        yield 'accumulate', 'like enabled, but the data is accumulated instead of written.'
        yield 'subtract', 'like enabled, but the data is subtracted instead of written.'
        yield 'set', 'like enabled, but bits that are written 1 are set in the register.'
        yield 'reset', 'like enabled, but bits that are written 1 are cleared in the register.'
        yield 'toggle', 'like enabled, but bits that are written 1 are toggled in the register.'

    @choice
    def after_hw_write():
        """Configures what happens after a hardware write."""
        yield 'nothing', 'no extra operation after write.'
        yield 'validate', 'register is automatically validated after write.'

    @choice
    def reset():
        """Configures the reset value."""
        yield False, 'the internal data register resets to 0, with the valid flag set.'
        yield True, 'the internal data register resets to 1, with the valid flag set.'
        yield None, 'the internal data register resets to 0, with the valid flag cleared.'
        yield int, 'the internal data register resets to the given value, with the valid flag set.'
        yield 'generic', 'the reset value is controlled through a VHDL generic.'

    @flag
    def ctrl_lock():
        """Controls the existence of the `ctrl_lock` control input signal. When
        this signal is asserted, writes are ignored."""

    @flag
    def ctrl_validate():
        """Controls the existence of the `ctrl_validate` control input signal.
        When this signal is asserted, the internal valid flag is set."""

    @flag
    def ctrl_invalidate():
        """Controls the existence of the `ctrl_invalidate` control input
        signal. When this signal is asserted, the internal valid flag is
        cleared. The data register is also set to 0."""

    @flag
    def ctrl_ready():
        """Controls the existence of the `ctrl_ready` control input signal.
        This signal behaves like an AXI stream ready signal for MMIO to stream
        fields."""

    @flag
    def ctrl_clear():
        """Controls the existence of the `ctrl_clear` control input
        signal. When this signal is asserted, the internal data register is
        cleared. The valid flag is not affected."""

    @flag
    def ctrl_reset():
        """Controls the existence of the `ctrl_reset` control input
        signal. When this signal is asserted, the field is reset, as if the
        register file `reset` input were asserted."""

    @flag
    def ctrl_increment():
        """Controls the existence of the `ctrl_increment` control input
        signal. When this signal is asserted, the internal data register is
        incremented."""

    @flag
    def ctrl_decrement():
        """Controls the existence of the `ctrl_decrement` control input
        signal. When this signal is asserted, the internal data register is
        decremented."""

    @flag
    def ctrl_bit_set():
        """Controls the existence of the `ctrl_bit_set` control input
        signal. This signal is as wide as the field is. When a bit in this
        input is high, the respective data bit is set."""

    @flag
    def ctrl_bit_clear():
        """Controls the existence of the `ctrl_bit_clear` control input
        signal. This signal is as wide as the field is. When a bit in this
        input is high, the respective data bit is cleared."""

    @flag
    def ctrl_bit_toggle():
        """Controls the existence of the `ctrl_bit_toggle` control input
        signal. This signal is as wide as the field is. When a bit in this
        input is high, the respective data bit is toggled."""

    @choice
    def drive_internal():
        """Configures driving an internal signal with the internal data
        register belonging to this field."""
        yield None, 'the feature is disabled.'
        yield (re.compile(r'[a-zA-Z][a-zA-Z0-9_]*'),
               'an internal signal with the given name is created and driven '
               'with the value in the internal data register for this field.')

    @choice
    def overrun_internal():
        """Configures strobing an internal signal when a bus write occurs while
        the stored value was already valid. This is equivalent to an overflow
        condition for MMIO to stream fields. It is intended to be used for
        overflow interrupts."""
        yield None, 'the feature is disabled.'
        yield (re.compile(r'[a-zA-Z][a-zA-Z0-9_]*'),
               'an internal signal with the given name is created (if '
               'necessary) and strobed when a bus write occurs while the '
               'internal valid signal is set.')

    @choice
    def underrun_internal():
        """Configures strobing an internal signal when a bus read occurs while
        the stored value is invalid. This is equivalent to an underflow
        condition for stream to MMIO fields. It is intended to be used for
        underflow interrupts."""
        yield None, 'the feature is disabled.'
        yield (re.compile(r'[a-zA-Z][a-zA-Z0-9_]*'),
               'an internal signal with the given name is created (if '
               'necessary) and strobed when a bus read occurs while the '
               'internal valid signal is cleared.')

    @choice
    def monitor_internal():
        """Configures monitoring an internal signal with this field."""
        yield None, 'the feature is disabled.'
        yield (re.compile(r'[a-zA-Z][a-zA-Z0-9_]*'),
               'the field monitors the internal signal with the given name. '
               '`monitor-mode` determines how the signal is used.')

    @choice
    def monitor_mode():
        """Configures how `monitor-internal` works. If `monitor-internal` is
        not specified, this key is no-op."""
        yield 'status', ('the internal data register is constantly assigned to '
                         'the vector-sized internal signal named by '
                         '`monitor-internal`.')
        yield 'bit-set', ('the internal data register is constantly or\'d with '
                          'the vector-sized internal signal named by '
                          '`monitor-internal`.')
        yield 'increment', ('the internal data register is incremented '
                            'whenever the respective bit in the repeat-sized '
                            'internal signal named by `monitor-internal` is '
                            'asserted.')


behavior_doc(
    'Constant fields for reading the design-time configuration of the '
    'hardware:', 1)

@derive(
    bus_read='enabled',
    after_bus_read='nothing',
    bus_write='disabled',
    after_bus_write='nothing',
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
    drive_internal=None,
    overrun_internal=None,
    underrun_internal=None,
    monitor_internal=None,
    monitor_mode='status',
    reset=None)
class _ReadOnly(Primitive):
    """Only used internally to prevent code repetition for all the
    overrides."""

@behavior(
    'constant', 'field which always reads as the same constant value.', 2)
@derive(name='`constant` behavior')
class Constant(_ReadOnly):
    """Fields with `constant` behavior always return the value specified
    through the `value` option when read. They cannot be written."""

    @checked
    def value(self, value):
        """Configures the value using an integer or boolean."""
        if not isinstance(value, int):
            ParseError.invalid('', value, 'an integer', 'a boolean')
        self.reset = value
        return value

@behavior(
    'config', 'field which always reads as the same value, configured through '
    'a generic.', 2)
@derive(name='`config` behavior', reset='generic')
class Config(_ReadOnly):
    """Fields with `config` behavior always return the value specified by a
    VHDL generic. They cannot be written."""


behavior_doc('Status fields for monitoring hardware:', 1)

@behavior(
    'status', 'field which always reflects the current state of an incoming '
    'signal.', 2)
@derive(name='`status` behavior', hw_write='status')
class Status(_ReadOnly):
    """Fields with `status` behavior always return the current state of an
    input port. They cannot be written."""

@behavior(
    'internal-status', 'field which always reflects the current state of an '
    'internal signal.', 2)
@derive(name='`internal-status` behavior')
class InternalStatus(_ReadOnly):
    """Fields with `internal-status` behavior always return the current state
    if an internal signal."""

    @checked
    def internal(self, value):
        """Configures the internal signal that is to be monitored. The value
        must be a string matching `[a-zA-Z][a-zA-Z0-9_]*`."""
        if not isinstance(value, str) or not re.fullmatch(r'[a-zA-Z][a-zA-Z0-9_]*', value):
            ParseError.invalid('', value, 'a string matching `[a-zA-Z][a-zA-Z0-9_]*`')
        self.monitor_internal = value
        return value

@behavior(
    'latching', 'status field that is only updated by hardware when a '
    'write-enable flag is set.', 2)
@derive(
    name='`latching` behavior',
    bus_read=['enabled'], # allow read to be disabled, or to wait for valid
    after_bus_read=['nothing'], # allow invalidation after read
    bus_write='disabled',
    after_bus_write='nothing',
    hw_read='disabled',
    hw_write='enabled',
    after_hw_write=['validate'], # allow disabling auto-validation
    ctrl_lock=False,
    ctrl_validate=[False], # allow control signals to be enabled
    ctrl_invalidate=[False],
    ctrl_ready=False,
    ctrl_clear=[False],
    ctrl_reset=[False],
    ctrl_increment=[False],
    ctrl_decrement=[False],
    ctrl_bit_set=[False],
    ctrl_bit_clear=[False],
    ctrl_bit_toggle=[False],
    drive_internal=None,
    overrun_internal=None,
    underrun_internal=None,
    monitor_internal=None,
    monitor_mode='status',
    reset=[None]) # default to invalid, allowing override
class Latching(Primitive):
    """The default behavior of `latching` fields is a lot like `status`, but
    the internal register is only updated when a write-enable flag is asserted.
    The associated valid bit is not used by default, but it can be, based on
    the configuration keys below. For instance, you can configure a latching
    field to block reads from it until the hardware first sets the value
    through the `bus-read` key."""

behavior_doc('Control fields for configuring hardware:', 1)

@behavior(
    'control', 'basic control field, i.e. written by software and read by '
    'hardware.', 2)
@derive(
    name='`control` behavior',
    bus_read=['enabled'],
    after_bus_read='nothing',
    bus_write='masked',
    after_bus_write='nothing',
    hw_read=['simple'],
    drive_internal=None,
    overrun_internal=None,
    underrun_internal=None,
    monitor_internal=None,
    monitor_mode='status')
class Control(Primitive):
    """This field behaves like a control register by default. That is, the
    MMIO bus interface is read/write, and the hardware interface is read-only.
    However, all behavior of the field can be overridden."""

@behavior(
    'internal-control', 'like `control`, but drives an internal signal.', 2)
@derive(
    name='`internal-control` behavior',
    bus_read=['enabled'],
    after_bus_read='nothing',
    bus_write='masked',
    after_bus_write='nothing',
    drive_internal=None,
    overrun_internal=None,
    underrun_internal=None,
    monitor_internal=None,
    monitor_mode='status')
class InternalControl(Primitive):
    """This field behaves like a control register that constrols an internal
    signal by default. That is, the MMIO bus interface is read/write, and the
    contents of the internal register drives an internal signal. The name of
    the internal signal must be set using `drive-internal`."""

    @checked
    def internal(self, value):
        """Configures the internal signal that is to be monitored. The value
        must be a string matching `[a-zA-Z][a-zA-Z0-9_]*`."""
        if not isinstance(value, str) or not re.fullmatch(r'[a-zA-Z][a-zA-Z0-9_]*', value):
            ParseError.invalid('', value, 'a string matching `[a-zA-Z][a-zA-Z0-9_]*`')
        self.drive_internal = value
        return value


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
    hw_read=['simple'],
    hw_write='nothing',
    after_hw_write='nothing',
    ctrl_bit_set=True,
    drive_internal=None,
    overrun_internal=None,
    underrun_internal=None,
    monitor_internal=None,
    monitor_mode='status')
class Flag(Primitive):
    """This field behaves like most edge/event-sensitive interrupt flags in
    peripherals work: occurance of the event sets the flag bit, and writing a
    one to the bit through MMIO clears it again. Usually there are more than
    one of these flags, combined into a single register. Canonical usage by
    software is then to read the register to determine which events have
    occurred, write the read value back to the register, and then handle the
    events that were found to have occurred. If new (different) events occur
    between the read and write, their flags will not be cleared, because a
    zero will be written to them by the write action. It is however not
    possible to detect how many of one kind of events have occurred. If this is
    necessary, the `counter` behavior can be used instead."""

@behavior(
    'volatile-flag', 'like `flag`, but implicitly cleared on read.', 2)
@derive(
    name='`volatile-flag` behavior',
    bus_read='enabled',
    after_bus_read='clear',
    ctrl_bit_set=True,
    hw_read=['simple'])
class VolatileFlag(Primitive):
    """This behavior is similar to `flag`, but the flags are immediately
    cleared when the field is read. This allows the field to be made read-only,
    allowing write-only registers to reside at the same address, and also makes
    the access procedure slightly faster. However, it requires read volatility,
    which means that the field cannot share a register with some other field
    types and. More importantly, it isn't compatible with processors/caches that
    prefetch values; any infrastructure that may perform spurious reads may
    inadvertantly clear the flags."""

@behavior(
    'internal-flag', 'like `flag`, but set by an internal signal.', 2)
@derive(
    name='`internal-flag` behavior',
    bus_read='enabled',
    bus_write='bit-clear',
    monitor_mode='bit-set',
    monitor_internal=None)
class InternalFlag(Primitive):
    """This field behaves like `flag`, but instead of the flag being set by an
    external signal, it is set by an internal signal. This may for instance be
    used in conjunction with the overrun output of an MMIO to stream field."""

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
    bus_read='enabled',
    after_bus_read='clear',
    monitor_mode='bit-set',
    monitor_internal=None)
class VolatileInternalFlag(Primitive):
    """This field behaves like `volatile-flag`, but instead of the flag being
    set by an external signal, it is set by an internal signal. This may for
    instance be used in conjunction with the overrun output of an MMIO to
    stream field."""

    @checked
    def internal(self, value):
        """Configures the internal signal that is to be monitored. The value
        must be a string matching `[a-zA-Z][a-zA-Z0-9_]*`."""
        if not isinstance(value, str) or not re.fullmatch(r'[a-zA-Z][a-zA-Z0-9_]*', value):
            ParseError.invalid('', value, 'a string matching `[a-zA-Z][a-zA-Z0-9_]*`')
        self.monitor_internal = value
        return value


behavior_doc('Flag-like fields for signalling requests from software to hardware:', 1)

@behavior(
    'strobe', 'one flag per bit, strobed by an MMIO write to signal some '
    'request to hardware.', 2)
@derive(
    name='`strobe` behavior',
    bus_read='disabled',
    bus_write='enabled',
    after_bus_write='invalidate',
    hw_read='simple')
class Strobe(Primitive):
    """This behavior may be used to signal a request to hardware, for hardware
    that can always handle the request immediately. When a 1 is written to a
    bit in this register, the respective output bit is strobed high for one
    cycle."""

@behavior(
    'request', 'like `strobe`, but the request flags stay high until '
    'acknowledged by hardware.', 2)
@derive(
    name='`request` behavior',
    bus_read=['enabled'],
    bus_write='bit-set',
    ctrl_bit_clear=True,
    hw_read='simple')
class Command(Primitive):
    """This field behaves like the inverse of a `flag`: the flags are set by
    software and cleared by hardware. They can be used for requests that cannot
    be handled immediately."""

@behavior(
    'multi-request', 'allows multiple software-to-hardware requests to be '
    'queued up atomically by counting.', 2)
@derive(
    name='`multi-request` behavior',
    bus_write='accumulate',
    hw_read=['simple'],
    ctrl_decrement=[True])
class MultiRequest(Primitive):
    """This field accumulates anything written to it, and by default allows
    hardware to decrement it. This may be used to request a certain number of
    things at once, in a way that doesn't break when multiple masters are
    requesting things at the same time."""


behavior_doc('Fields for counting events:', 1)

@behavior(
    'counter', 'external event counter, reset explicitly by a write.', 2)
@derive(
    name='`counter` behavior',
    bus_read='enabled',
    bus_write='subtract',
    ctrl_increment=[True],
    hw_read=['simple'])
class Counter(Primitive):
    """Similar to `flag` fields, `counter`s are used to signal events from
    hardware to software. However, counters allow multiple events occurring
    between consecutive software read cycles to be registered by counting
    instead of bit-setting. Like `flag`, software should use fields of this
    type by reading the value and then writing the read value to it in order
    to avoid missing events; the write operation subtracts the written value
    from the internal register."""

@behavior(
    'volatile-counter', 'external event counter, reset implicitly by the '
    'read.', 2)
@derive(
    name='`volatile-counter` behavior',
    bus_read='enabled',
    after_bus_read='clear',
    ctrl_increment=[True],
    hw_read=['simple'])
class VolatileCounter(Primitive):
    """This behavior is similar to `counter`, but the counter value is
    immediately cleared when the field is read. This allows the field to be
    made read-only, allowing write-only registers to reside at the same
    address, and also makes the access procedure slightly faster. However, it
    requires read volatility, which means that the field cannot share a
    register with some other field types and. More importantly, it isn't
    compatible with processors/caches that prefetch values; any infrastructure
    that may perform spurious reads may inadvertantly clear the flags."""

@behavior(
    'internal-counter', 'internal event counter, reset explicitly by a write.', 2)
@derive(
    name='`counter` behavior',
    bus_read='enabled',
    bus_write='subtract',
    monitor_mode='increment',
    monitor_internal=None,
    hw_read=['simple'])
class InternalCounter(Primitive):
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
    bus_read='enabled',
    after_bus_read='clear',
    monitor_mode='increment',
    monitor_internal=None,
    hw_read=['simple'])
class VolatileInternalCounter(Primitive):
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

