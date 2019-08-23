"""Control field behaviors for configuring hardware."""

import re
from ...configurable import derive, checked, ParseError
from .registry import behavior, behavior_doc
from .primitive import BasePrimitive

behavior_doc('Control fields for configuring hardware:', 1)

@derive(
    name='`control` behavior',
    bus_read=('enabled', 'error', 'disabled'),
    after_bus_read='nothing',
    bus_write=('masked', 'enabled', 'invalid', 'invalid-only'),
    after_bus_write=('nothing', 'validate'),
    hw_write='disabled',
    after_hw_write='nothing',
    ctrl_validate=False,
    ctrl_ready=False,
    ctrl_clear=False,
    ctrl_increment=False,
    ctrl_decrement=False,
    ctrl_bit_set=False,
    ctrl_bit_clear=False,
    ctrl_bit_toggle=False,
    reset=[None])
class BaseControl(BasePrimitive):
    """Base class for control registers."""

@behavior(
    'control', 'basic control field, i.e. written by software and read by '
    'hardware.', 2)
@derive(
    hw_read=('simple', 'enabled'),
    reset=[None])
class Control(BaseControl):
    """Fields with `control` behavior are used to push runtime configuration
    values from software to hardware. They are normally read-write on the MMIO
    bus and respect the AXI4L byte strobe bits so they can be easily (though
    not necessarily atomically) updated partially, but read access can be
    disabled and write access can be simplified if this is desirable.

    The hardware interface by default consists of just an `std_logic` or
    `std_logic_vector` with the current value of the field, but you can also
    enable a valid bit by setting `hw-read` to `enabled` if you so desire.
    You'll also need to set `bus-write` to `enabled` and `after-bus-write` to
    `validate` to make that work as you would expect: the value will be marked
    invalid from reset to when it's first written. You can also make the field
    one-time-programmable by selecting `invalid` or `invalid-only` for
    `bus-write` instead of `enabled`."""

@behavior(
    'internal-control', 'like `control`, but drives an internal signal.', 2)
@derive(
    name='`internal-control` behavior',
    bus_write=('masked', 'enabled'),
    after_bus_write='nothing',
    hw_read='disabled',
    ctrl_lock=False,
    ctrl_invalidate=False,
    ctrl_reset=False,
    reset=(False, True, int, 'generic'))
class InternalControl(BaseControl):
    """This field behaves like a control register that constrols an internal
    signal by default. That is, the MMIO bus interface is read/write, and the
    contents of the internal register drives an internal signal. The name of
    the internal signal must be set using `drive-internal`."""

    @checked
    def internal(self, value):
        """Configures the internal signal that is to be driven. The value
        must be a string matching `[a-zA-Z][a-zA-Z0-9_]*`."""
        if not isinstance(value, str) or not re.fullmatch(r'[a-zA-Z][a-zA-Z0-9_]*', value):
            ParseError.invalid('', value, 'a string matching `[a-zA-Z][a-zA-Z0-9_]*`')
        self.drive_internal = value
        return value
