"""Flag-like field behaviors for signalling events from hardware to
software."""

from ...configurable import derive
from .registry import behavior, behavior_doc
from .primitive import Primitive

behavior_doc('Fields for interfacing with AXI streams:', 1)

@behavior(
    'stream-to-mmio', 'field which pops data from an incoming stream.', 2)
@derive(
    name='`stream-to-mmio` behavior',
    bus_read=(
        ('enabled', 'reads from an empty holding register return 0.'),
        ('valid-only', 'reads from an empty holding register return a slave '
         'error.'),
        ('valid-wait', 'reads from an empty holding register are blocked '
         'until data is received from the stream.')),
    after_bus_read='invalidate',
    bus_write='disabled',
    after_bus_write='nothing',
    hw_read='handshake',
    hw_write='stream',
    after_hw_write='validate',
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
    overflow_internal=None,
    underflow_internal=None,
    bit_overflow_internal=None,
    bit_underflow_internal=None,
    overrun_internal=None,
    monitor_internal=None,
    monitor_mode='status',
    reset=(None, False, True, int, 'generic'))
class StreamToMMIO(Primitive):
    """Fields with `stream-to-mmio` behavior interface with an incoming AXI4
    stream. When the incoming AXI4 stream is valid and the internal register
    for the field is not, the stream is handshaked and the data is put in the
    register. The MMIO bus can then read from the field to fetch the data,
    automatically invalidating the internal register to let the cycle repeat.
    The field cannot be written by the bus.

    By default, the only way for software to know whether data is waiting in
    the internal holding register is to read and compare with zero, which is
    always what's returned for an empty holding register. This is of course
    not ideal at best. `vhdmmio` provides several options for doing this
    better, which require a bit more work:

     - Set `bus-read` to `valid-wait`. In this case, reads will always return
       valid data because they are blocked until data is available. This is
       the simplest method, but reading from a stream that isn't going to send
       anything will deadlock the whole bus.
     - Set `bus-read` to `valid-only`. In this case, a read from an empty
       holding register yields a slave error. This is very simple from
       `vhdmmio`'s standpoint, but requires the bus master to actually support
       AXI4L error conditions in a convenient way.
     - Drive an internal signal with the status of the holding register
       (`full-internal` or `empty-internal`), and monitor it with a status
       field (`internal-status` behavior) and/or an internal interrupt.
     - Strobe an internal signal when an invalid bus read occurs using
       `underrun-internal` and check whether an underrun occurred after the
       fact using a status field (`internal-flag` behavior) and/or an internal
       interrupt.

    Finally, `vhdmmio` allows you to set the reset value of the internal
    register to a valid value. This effectively imitates a stream transfer,
    which may be used to start some loop based on sending stream transfers
    back and forth between systems."""

@behavior(
    'mmio-to-stream', 'field which pushes data into an outgoing stream.', 2)
@derive(
    name='`mmio-to-stream` behavior',
    bus_read='disabled',
    after_bus_read='nothing',
    bus_write=(
        ('invalid', 'writes to a full holding register are silently ignored.'),
        ('enabled', 'writes to a full holding register override the register. '
         'NOTE: this is not AXI4-stream compliant behavior, since `data` must '
         'remain stable between validation and the completed handshake.'),
        ('invalid-wait', 'writes to a full holding register are blocked until '
         'the register is popped by the stream.'),
        ('invalid-only', 'writes to a full holding register return a slave '
         'error.')),
    after_bus_write='validate',
    hw_read='enabled',
    hw_write='disabled',
    after_hw_write='nothing',
    ctrl_lock=False,
    ctrl_validate=False,
    ctrl_invalidate=False,
    ctrl_ready=True,
    ctrl_clear=False,
    ctrl_reset=False,
    ctrl_increment=False,
    ctrl_decrement=False,
    ctrl_bit_set=False,
    ctrl_bit_clear=False,
    ctrl_bit_toggle=False,
    drive_internal=None,
    overflow_internal=None,
    underflow_internal=None,
    bit_overflow_internal=None,
    bit_underflow_internal=None,
    underrun_internal=None,
    monitor_internal=None,
    monitor_mode='status',
    reset=(None, False, True, int, 'generic'))
class MMIOToStream(Primitive):
    """Fields with `mmio-to-stream` behavior interface with an outgoing AXI4
    stream. When the field is written, the written data is placed in the
    field's internal data register and the stream is validated. A completed
    handshake invalidates the internal data register, allowing the MMIO bus
    master to write the next value. The field cannot be read by the bus.

    By default, there is no way for software to know whether the holding
    register is ready for the next datum. This is not a problem if flow
    control is handled by some other means. However, `vhdmmio` also provides
    several methods to achieve proper flow control:

     - Set `bus-write` to `invalid-wait`. In this case, writes are blocked
       until the holding register is ready. This is the simplest flow control
       method, but writing to a stream that isn't going to acknowledge anything
       will deadlock the whole bus.
     - Set `bus-write` to `invalid-only`. In this case, writing to a full
       holding register yields a slave error. This is very simple from
       `vhdmmio`'s standpoint, but requires the bus master to actually support
       AXI4L error conditions in a convenient way.
     - Drive an internal signal with the status of the holding register
       (`full-internal` or `empty-internal`), and monitor it with a status
       field (`internal-status` behavior) and/or an internal interrupt.
     - Strobe an internal signal when an invalid bus write occurs using
       `overrun-internal` and check whether an overrun occurred after the
       fact using a status field (`internal-flag` behavior) and/or an internal
       interrupt.

    Finally, `vhdmmio` allows you to set the reset value of the internal
    register to a valid value. This effectively imitates a stream transfer,
    which may be used to start some loop based on sending stream transfers
    back and forth between systems."""
