"""Submodule for primitive behavior."""

from .base import Behavior, behavior, BusAccessNoOpMethod, BusAccessBehavior, BusBehavior
from ...config.behavior import Primitive

@behavior(Primitive)
class PrimitiveBehavior(Behavior):
    """Behavior class for primitive fields."""

    def __init__(self, resources, field_descriptor,
                 behavior_cfg, read_allow_cfg, write_allow_cfg):

        # Ensure that post-access operations are set to "nothing" when they are
        # not supported.
        if behavior_cfg.bus_read in ('disabled', 'error'):
            if behavior_cfg.after_bus_read != 'nothing':
                raise ValueError('bus read mode "%s" cannot be combined with a '
                                 'post-read operation' % behavior_cfg.bus_read)

        if behavior_cfg.bus_write in ('disabled', 'error', 'masked'):
            if behavior_cfg.after_bus_write != 'nothing':
                raise ValueError('bus write mode "%s" cannot be combined with a '
                                 'post-write operation' % behavior_cfg.bus_write)

        if behavior_cfg.hw_write in ('disabled', 'status'):
            if behavior_cfg.after_hw_write != 'nothing':
                raise ValueError('hardware write mode "%s" cannot be combined with a '
                                 'post-write operation' % behavior_cfg.hw_write)

        # The underrun and overrun internals only make sense when the field can
        # be read or written respectively.
        if behavior_cfg.bus_read in ('disabled', 'error'):
            if behavior_cfg.underrun_internal is not None:
                raise ValueError('bus read mode "%s" cannot be combined with an '
                                 'underrun internal' % behavior_cfg.bus_read)
        if behavior_cfg.bus_write in ('disabled', 'error', 'masked'):
            if behavior_cfg.overrun_internal is not None:
                raise ValueError('bus write mode "%s" cannot be combined with an '
                                 'overrun internal' % behavior_cfg.bus_write)

        # The lock control signal only affects bus writes, so it doesn't make
        # sense if the bus cannot write.
        if behavior_cfg.bus_write in ('disabled', 'error'):
            if behavior_cfg.ctrl_lock:
                raise ValueError('bus write mode "%s" cannot be combined with a '
                                 'lock control signal' % behavior_cfg.bus_write)

        # If the field is a status field, ensure that nothing else is trying to
        # write to it.
        is_int_stat = (
            behavior_cfg.monitor_internal is not None
            and behavior_cfg.monitor_mode == 'status')
        is_ext_stat = behavior_cfg.hw_write == 'status'
        if is_int_stat or is_ext_stat:
            if is_int_stat and is_ext_stat:
                raise ValueError('status field source cannot be both internal '
                                 'and external at the same time')
            if behavior_cfg.after_bus_read != 'nothing':
                raise ValueError('status fields cannot be combined with a '
                                 'post-read operation')
            if behavior_cfg.bus_write not in ('disabled', 'error'):
                raise ValueError('status fields cannot be combined with a '
                                 'bus write operation')
            if is_int_stat and behavior_cfg.hw_write != 'disabled':
                raise ValueError('internal status fields cannot be combined with a '
                                 'hardware write operation')
            for ctrl_signal in (
                    'validate', 'invalidate', 'ready', 'clear', 'reset',
                    'increment', 'decrement', 'bit_set', 'bit_clear', 'bit_toggle'):
                if getattr(behavior_cfg, 'ctrl_%s' % ctrl_signal):
                    raise ValueError('status fields cannot be combined with a '
                                     '%s control signal' % ctrl_signal)
            if is_ext_stat and behavior_cfg.monitor_internal is not None:
                raise ValueError('external status fields cannot be combined with an '
                                 'internal monitor signal')

        # Figure out the reset value for the documentation.
        if is_int_stat or is_ext_stat:
            self._doc_reset = None
        elif behavior_cfg.reset is None:
            self._doc_reset = 0
        elif behavior_cfg.reset == 'generic':
            self._doc_reset = None
        else:
            self._doc_reset = int(behavior_cfg.reset)

        # The `stream` write mode (stream to MMIO) cannot be combined with
        # hardware read, because both produce a `data` port (in opposite
        # direction). The `valid` signal of the full hardware read interface
        # would also conflict. Similarly, the `handshake` hardware read mode
        # cannot be combined with the ready control signal.
        if behavior_cfg.hw_write == 'stream':
            if behavior_cfg.hw_read == 'enabled':
                raise ValueError('cannot combine stream hardware write mode with '
                                 'full hardware read mode (name conflict for `data` '
                                 'and `valid` signals)')
            if behavior_cfg.hw_read == 'simple':
                raise ValueError('cannot combine stream hardware write mode with '
                                 'simple hardware read mode (name conflict for `data` '
                                 'signals)')
        if behavior_cfg.hw_read == 'handshake' and behavior_cfg.ctrl_ready:
            raise ValueError('cannot combine handshake hardware read mode with '
                             'ready control signal (name conflict for `ready` '
                             'signals)')

        # Register any internal signals used by this behavior.
        def drive_internal(name):
            if name is None:
                return None
            if field_descriptor.is_vector():
                raise ValueError('repeated fields cannot drive an internal signal')
            return resources.internals.drive(
                field_descriptor, name, field_descriptor.base_bitrange.shape)

        def strobe_internal(name):
            if name is None:
                return None
            if field_descriptor.is_vector():
                raise ValueError('repeated fields cannot strobe an internal signal')
            return resources.internals.strobe(
                field_descriptor, name, field_descriptor.base_bitrange.shape)

        def monitor_internal(name):
            if name is None:
                return None
            if field_descriptor.is_vector():
                raise ValueError('repeated fields cannot monitor an internal signal')
            return resources.internals.use(
                field_descriptor, name, field_descriptor.base_bitrange.shape)

        def drive_flag_internal(name):
            if name is None:
                return None
            return resources.internals.drive(
                field_descriptor, name, field_descriptor.shape)

        def strobe_flag_internal(name):
            if name is None:
                return None
            return resources.internals.strobe(
                field_descriptor, name, field_descriptor.shape)

        def monitor_flag_internal(name):
            if name is None:
                return None
            return resources.internals.use(
                field_descriptor, name, field_descriptor.shape)

        if behavior_cfg.after_bus_write == 'invalidate':
            self._drive_internal = strobe_internal(behavior_cfg.drive_internal)
        else:
            self._drive_internal = drive_internal(behavior_cfg.drive_internal)
        self._full_internal = drive_flag_internal(behavior_cfg.full_internal)
        self._empty_internal = drive_flag_internal(behavior_cfg.empty_internal)
        self._overflow_internal = strobe_flag_internal(behavior_cfg.overflow_internal)
        self._underflow_internal = strobe_flag_internal(behavior_cfg.underflow_internal)
        self._bit_overflow_internal = strobe_flag_internal(behavior_cfg.bit_overflow_internal)
        self._bit_underflow_internal = strobe_flag_internal(behavior_cfg.bit_underflow_internal)
        self._overrun_internal = strobe_flag_internal(behavior_cfg.overrun_internal)
        self._underrun_internal = strobe_flag_internal(behavior_cfg.underrun_internal)
        if behavior_cfg.monitor_mode == 'increment':
            self._monitor_internal = monitor_flag_internal(behavior_cfg.monitor_internal)
        else:
            self._monitor_internal = monitor_internal(behavior_cfg.monitor_internal)

        # Determine the bus read behavior.
        if behavior_cfg.bus_read == 'disabled':
            read_behavior = None
            can_read_for_rmw = False
        else:
            volatile = False
            no_op_method = BusAccessNoOpMethod.ALWAYS
            blocking = behavior_cfg.bus_read == 'valid-wait'
            can_read_for_rmw = behavior_cfg.bus_read != 'error'

            if behavior_cfg.after_bus_read != 'nothing':
                volatile = True
                no_op_method = BusAccessNoOpMethod.NEVER

            read_behavior = BusAccessBehavior(
                read_allow_cfg,
                volatile=volatile,
                blocking=blocking,
                no_op_method=no_op_method)

        # Determine the bus write behavior.
        if behavior_cfg.bus_write == 'disabled':
            write_behavior = None
        else:
            volatile, no_op_method = {
                'error': (False, BusAccessNoOpMethod.NEVER),
                'enabled': (False, BusAccessNoOpMethod.WRITE_CURRENT),
                'invalid': (False, BusAccessNoOpMethod.WRITE_CURRENT),
                'invalid-wait': (False, BusAccessNoOpMethod.WRITE_CURRENT),
                'invalid-only': (False, BusAccessNoOpMethod.WRITE_CURRENT),
                'masked': (False, BusAccessNoOpMethod.WRITE_CURRENT_OR_MASK),
                'accumulate': (True, BusAccessNoOpMethod.WRITE_ZERO),
                'subtract': (True, BusAccessNoOpMethod.WRITE_ZERO),
                'bit-set': (behavior_cfg.bit_overflow_internal is not None,
                            BusAccessNoOpMethod.WRITE_ZERO),
                'bit-clear': (behavior_cfg.bit_underflow_internal is not None,
                              BusAccessNoOpMethod.WRITE_ZERO),
                'bit-toggle': (True, BusAccessNoOpMethod.WRITE_ZERO),
            }[behavior_cfg.bus_write]
            blocking = behavior_cfg.bus_write == 'invalid-wait'

            if behavior_cfg.after_bus_write != 'nothing':
                volatile = True
                no_op_method = BusAccessNoOpMethod.NEVER

            write_behavior = BusAccessBehavior(
                write_allow_cfg,
                volatile=volatile,
                blocking=blocking,
                no_op_method=no_op_method)

        bus_behavior = BusBehavior(read_behavior, write_behavior, can_read_for_rmw)

        super().__init__(field_descriptor, behavior_cfg, bus_behavior)

    @property
    def drive_internal(self):
        """The internal signal driven by this field, or `None` if there is no
        such signal."""
        return self._drive_internal

    @property
    def full_internal(self):
        """The internal signal that is driven by this field to indicate that it
        is "full" (the register is valid), or `None` if there is no such
        signal. The shape of the internal is the shape of the field descriptor,
        so repeated fields should index it by their field index."""
        return self._full_internal

    @property
    def empty_internal(self):
        """The internal signal that is driven by this field to indicate that it
        is "empty" (the register is invalid), or `None` if there is no such
        signal. The shape of the internal is the shape of the field descriptor,
        so repeated fields should index it by their field index."""
        return self._empty_internal

    @property
    def overflow_internal(self):
        """The internal signal that is strobed by this field when an unsigned
        integer overflow occurs, or `None` if there is no such signal. The
        shape of the internal is the shape of the field descriptor, so repeated
        fields should index it by their field index."""
        return self._overflow_internal

    @property
    def underflow_internal(self):
        """The internal signal that is strobed by this field when an unsigned
        integer underflow occurs, or `None` if there is no such signal. The
        shape of the internal is the shape of the field descriptor, so repeated
        fields should index it by their field index."""
        return self._underflow_internal

    @property
    def bit_overflow_internal(self):
        """The internal signal that is strobed by this field when an bit
        overflow occurs (a high bit is written high using a bit-set operation),
        or `None` if there is no such signal. The shape of the internal is the
        shape of the field descriptor, so repeated fields should index it by
        their field index."""
        return self._bit_overflow_internal

    @property
    def bit_underflow_internal(self):
        """The internal signal that is strobed by this field when an bit
        underflow occurs (a low bit is written low using a bit-clear
        operation), or `None` if there is no such signal. The shape of the
        internal is the shape of the field descriptor, so repeated fields
        should index it by their field index."""
        return self._bit_underflow_internal

    @property
    def overrun_internal(self):
        """The internal signal that is strobed by this field when an overrun
        occurs (the register is validated while it is already valid), or `None`
        if there is no such signal. The shape of the internal is the shape of
        the field descriptor, so repeated fields should index it by their field
        index."""
        return self._overrun_internal

    @property
    def underrun_internal(self):
        """The internal signal that is strobed by this field when an underrun
        occurs (the register is invalidated while it is already invalid), or
        `None` if there is no such signal. The shape of the internal is the
        shape of the field descriptor, so repeated fields should index it by
        their field index."""
        return self._underrun_internal

    @property
    def monitor_internal(self):
        """The internal signal that is monitored by this field, or `None` if
        there is no such signal. If the monitoring method is set to
        `'increment'`, the shape of the internal is the
        shape of the field descriptor, so repeated fields should index it by
        their field index. Otherwise, the signal takes the shape of the field
        itself."""
        return self._monitor_internal

    @property
    def doc_reset(self):
        """The reset value as printed in the documentation as an integer, or
        `None` if the field is driven by a signal and thus does not have a
        register to reset."""
        return self._doc_reset
