"""Submodule for `Primitive` configurable."""

import re
from ...configurable import configurable, Configurable, flag, choice, derive
from .registry import behavior

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
        yield 'increment', 'register is incremented after read, valid untouched.'
        yield 'decrement', 'register is decremented after read, valid untouched.'

    @choice
    def bus_write():
        """Configures what happens when a bus write occurs."""
        yield 'disabled', 'write access is disabled.'
        yield 'error', 'writes always return a slave error.'
        yield 'enabled', 'normal write access to register. Masked bits are written 0.'
        yield 'invalid', 'as above, but ignores the write when the register is valid.'
        yield 'invalid-wait', 'as above, but blocks until register is invalid.'
        yield 'invalid-only', 'as above, but fails when register is already valid.'
        yield 'masked', 'write access respects strobe bits. Precludes after-bus-write.'
        yield 'accumulate', 'write data is added to the register.'
        yield 'subtract', 'write data is subtracted from the register.'
        yield 'bit-set', 'bits that are written 1 are set in the register.'
        yield 'bit-clear', 'bits that are written 1 are cleared in the register.'
        yield 'bit-toggle', 'bits that are written 1 are toggled in the register.'

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
        yield 'simple', 'only the data output is generated.'
        yield 'enabled', 'both a data and a valid output signal are generated.'
        yield 'handshake', 'a stream-to-mmio ready signal is generated.'

    @choice
    def hw_write():
        """Configure the existence and behavior of the hardware write port."""
        yield 'disabled', 'no write port is generated.'
        yield 'status', 'the register is constantly driven by a port and is always valid.'
        yield 'enabled', 'a record consisting of a write enable flag and data is generated.'
        yield 'stream', ('like enabled, but the write only occurs when the register is invalid. '
                         'Furthermore, the `write_data` signal is renamed to `data`, and the '
                         '`write_enable` signal is renamed to `valid`, in order to comply with '
                         'AXI-stream naming conventions.')
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
        """Configures driving or strobing an internal signal with the internal
        data register belonging to this field. The signal is strobed when
        `after-bus-write` is set to `invalidate`, otherwise it is driven."""
        yield None, 'the feature is disabled.'
        yield (re.compile(r'[a-zA-Z][a-zA-Z0-9_]*'),
               'an internal signal with the given name is created and driven '
               'with the value in the internal data register for this field.')

    @choice
    def full_internal():
        """Configures driving an internal signal high when the internal data
        register is valid. This essentially serves as a holding register full
        signal for stream interface fields."""
        yield None, 'the feature is disabled.'
        yield (re.compile(r'[a-zA-Z][a-zA-Z0-9_]*'),
               'an internal signal with the given name is created (if '
               'necessary) and driven by the internal valid register of this '
               'field.')
    @choice
    def empty_internal():
        """Configures driving an internal signal high when the internal data
        register is invalid. This essentially serves as a holding register
        empty signal for stream interface fields."""
        yield None, 'the feature is disabled.'
        yield (re.compile(r'[a-zA-Z][a-zA-Z0-9_]*'),
               'an internal signal with the given name is created (if '
               'necessary) and driven by the one\'s complement of the '
               'internal valid register of this field.')

    @choice
    def overflow_internal():
        """Configures strobing an internal signal when the most significant bit
        of the internal register flips from high to low during an increment or
        accumulate operation. This essentially serves as an overflow signal for
        counter fields."""
        yield None, 'the feature is disabled.'
        yield (re.compile(r'[a-zA-Z][a-zA-Z0-9_]*'),
               'an internal signal with the given name is created (if '
               'necessary) and strobed when an increment or accumulate '
               'operation causes the MSB of the data register to be cleared.')

    @choice
    def underflow_internal():
        """Configures strobing an internal signal when the most significant bit
        of the internal register flips from low to high during a decrement or
        subtract operation. This essentially serves as an underflow signal for
        counter fields."""
        yield None, 'the feature is disabled.'
        yield (re.compile(r'[a-zA-Z][a-zA-Z0-9_]*'),
               'an internal signal with the given name is created (if '
               'necessary) and strobed when a decrement or subtract '
               'operation causes the MSB of the data register to be set.')

    @choice
    def bit_overflow_internal():
        """Configures strobing an internal signal when a bit-set operation to
        a bit that was already set occurs. This essentially serves as an
        overflow signal for flag fields."""
        yield None, 'the feature is disabled.'
        yield (re.compile(r'[a-zA-Z][a-zA-Z0-9_]*'),
               'an internal signal with the given name is created (if '
               'necessary) and strobed when a bit-set operation occurs to '
               'an already-set bit.')

    @choice
    def bit_underflow_internal():
        """Configures strobing an internal signal when a bit-clear operation to
        a bit that was already cleared occurs. This essentially serves as an
        underflow signal for flag fields."""
        yield None, 'the feature is disabled.'
        yield (re.compile(r'[a-zA-Z][a-zA-Z0-9_]*'),
               'an internal signal with the given name is created (if '
               'necessary) and strobed when a bit-clear operation occurs to '
               'an already-cleared bit.')

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


@derive(
    drive_internal=None,
    full_internal=None,
    empty_internal=None,
    overflow_internal=None,
    underflow_internal=None,
    bit_overflow_internal=None,
    bit_underflow_internal=None,
    overrun_internal=None,
    underrun_internal=None,
    monitor_internal=None,
    monitor_mode='status')
class BasePrimitive(Primitive):
    """Only used internally to minimize override code repetition."""


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
    reset=None)
class ReadOnlyPrimitive(BasePrimitive):
    """Only used internally to minimize override code repetition."""
