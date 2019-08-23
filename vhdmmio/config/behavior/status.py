"""Status-like specializations of `Primitive` for monitoring hardware."""

import re
from ...configurable import derive, checked, ParseError
from .registry import behavior, behavior_doc
from .primitive import ReadOnlyPrimitive, BasePrimitive

behavior_doc('Status fields for monitoring hardware:', 1)

@behavior(
    'status', 'field which always reflects the current state of an incoming '
    'signal.', 2)
@derive(name='`status` behavior', hw_write='status')
class Status(ReadOnlyPrimitive):
    """Fields with `status` behavior always return the current state of an
    input port. They cannot be written."""

@behavior(
    'internal-status', 'field which always reflects the current state of an '
    'internal signal.', 2)
@derive(name='`internal-status` behavior')
class InternalStatus(ReadOnlyPrimitive):
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
    bus_read=('enabled', 'valid-wait', 'valid-only'),
    after_bus_read=('nothing', 'invalidate', 'clear'),
    bus_write='disabled',
    after_bus_write='nothing',
    hw_read='disabled',
    hw_write='enabled',
    ctrl_lock=False,
    ctrl_ready=False,
    reset=[None]) # default to invalid, allowing override
class Latching(BasePrimitive):
    """The `latching` behavior is a lot like `status`, but more advanced. It is
    used when status information is not always available, but only updated
    sporadically through a write enable. This means that there is an "invalid"
    state of some kind, used before the first status value is received. By
    default fields with this behavior will just read as 0 in this state, but
    this behavior can be overridden with the options below. For instance, the
    field can be configured to block the read access until the status is valid.
    It's also possible to enable a control signal that invalidates the field on
    demand, or to invalidate on read."""
