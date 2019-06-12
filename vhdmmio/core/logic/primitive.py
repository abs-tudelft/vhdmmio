from vhdmmio.core.field import FieldLogic, field_logic
from vhdmmio.core.accesscaps import AccessCapabilities

def _choice(dictionary, key, values):
    value = dictionary.pop(key, values[0])
    if value not in values:
        raise ValueError('%s must be one of %s' % (key, ', '.join(values)))
    return value

def _switches(dictionary, key, values):
    switches = dictionary.pop(key, [])
    if not isinstance(switches, list):
        raise ValueError('%s must be a list of strings' % key)
    for switch in switches:
        if switch not in values:
            raise ValueError('values for %s must be one of %s' % (key, ', '.join(values)))
    switches = set(switches)

    for value in values:
        switch = dictionary.pop(key, False)
        if switch == 'enabled':
            switch = True
        elif switch == 'disabled':
            switch = False
        if not isinstance(switch, bool):
            raise ValueError('%s-%s must be a boolean' % (key, value))
        if switch:
            switches.add(value)

    return switches

@field_logic('primitive')
class ControlField(FieldLogic):
    def __init__(self, field_descriptor, dictionary):

        # Configures what happens when a read occurs.
        self._bus_read = _choice(dictionary, 'bus-read', [
            'disabled',     # Read access is disabled.
            'error',        # Reads always return a slave error.
            'enabled',      # Normal read access to register.
            'valid-wait',   # As above, but blocks until register is valid.
            'valid-only'])  # As above, but fails when register is not valid yet.

        # Configures what happens to the register after the read.
        self._after_bus_read = _choice(dictionary, 'after-bus-read', [
            'nothing',      # No extra operation after read.
            'invalidate',   # Register is invalidated after read.
            'clear',        # Register is cleared and invalidated after read.
            'increment',    # Register is incremented after read.
            'decrement'])   # Register is decremented after read.

        # Configures what happens when a write occurs.
        self._bus_write = _choice(dictionary, 'bus-write',
            'disabled',     # Write access is disabled.
            'error',        # Writes always return a slave error.
            'enabled',      # Normal write access to register. Masked bits are written 0.
            'invalid-wait', # As above, but blocks until register is invalid.
            'invalid-only', # As above, but fails when register is already valid.
            'masked',       # Write access respects strobe bits. Precludes after-bus-write.
            'accumulate',   # Write data is added to the register.
            'set',          # Bits that are written 1 are set in the register.
            'reset',        # Bits that are written 1 are cleared in the register.
            'toggle')       # Bits that are written 1 are toggled in the register.

        # Configures what happens after a write occurs. Clear is special in
        # that it happens after the new value is pushed to the hardware read,
        # so it can be used to create a strobe register. The other operations
        # happen immediately after the write.
        self._after_bus_write = _choice(dictionary, 'after-bus-write', [
            'nothing',      # No extra operation after write.
            'validate',     # Register is validated after write.
            'clear',        # Register is cleared and invalidated after write.
            'increment',    # Register is incremented after write.
            'decrement'])   # Register is decremented after write.

        # Configure hardware read port.
        self._hw_read = _choice(dictionary, 'hw-read', [
            'disabled',     # No read port is generated.
            'simple',       # Only a simple data port is generated (no record).
            'enabled'])     # A record of the data and valid bit is generated.

        # Configure hardware write port.
        self._hw_write = _choice(dictionary, 'hw-write',
            'disabled',     # No write port is generated.
            'status',       # The register is constantly driven by a port and is always valid.
            'enabled',      # A record consisting of a write enable flag and data is generated.
            'accumulate',   # As above, but the data is accumulated instead of written.
            'set',          # As above, but bits that are written 1 are set in the register.
            'reset',        # As above, but bits that are written 1 are cleared in the register.
            'toggle')       # As above, but bits that are written 1 are toggled in the register.

        # Configures what happens after a hardware write occurs.
        self._after_hw_write = _choice(dictionary, 'after-hw-write', [
            'nothing',      # No extra operation after write.
            'validate',     # Register is validated after write.
            'clear',        # Register is cleared and invalidated after write.
            'increment',    # Register is incremented after write.
            'decrement'])   # Register is decremented after write.

        # The following switches add an extra write port record.
        self._ctrl = _switches(dictionary, 'ctrl', [
            'validate',     # Adds a strobe signal that validates the register.
            'invalidate',   # Adds a strobe signal that invalidates the register.
            'clear',        # Adds a strobe signal that clears the register (sets value to 0).
            'reset',        # Adds a strobe signal that works just like a global reset.
            'increment',    # Adds a strobe signal that increments the register.
            'decrement',    # Adds a strobe signal that decrements the register.
            'bit-set',      # Adds a vector of strobe signals that set bits in the register.
            'bit-clear',    # Adds a vector of strobe signals that reset bits in the register.
            'bit-toggle'])  # Adds a vector of strobe signals that toggle bits in the register.

        # Configures the reset value:
        #  - specify an integer to indicate that the field should have the
        #    given value after reset and be valid.
        #  - specify "generic" to generate a generic that specifies the initial
        #    value of the register.
        #  - specify null/None to indicate that the field should be invalid
        #    after reset.
        rst = dictionary.pop('reset', 0)
        if rst is not None and rst != 'generic' and not isinstance(rst, int):
            raise ValueError('reset must be an integer, "generic", or null')
        self._reset = rst

        # Validate the field configuration.
        if self._bus_read in ('disabled', 'error'):
            if self._after_bus_read != 'nothing':
                raise ValueError('bus read mode "%s" cannot be combined with a '
                                'post-read operation' % self._bus_read)

        if self._bus_write in ('disabled', 'error', 'masked'):
            if self._after_bus_write != 'nothing':
                raise ValueError('bus write mode "%s" cannot be combined with a '
                                'post-write operation' % self._bus_write)

        if self._hw_write in ('disabled', 'status'):
            if self._after_hw_write != 'nothing':
                raise ValueError('hardware write mode "%s" cannot be combined with a '
                                'post-write operation' % self._hw_write)

        if self._hw_write == 'status':
            if self._ctrl:
                raise ValueError('status fields cannot have control registers')
            if self._bus_write not in ('disabled', 'error'):
                raise ValueError('status fields cannot allow bus writes')

        super().__init__(
            field_descriptor=field_descriptor,
            read_caps=read_caps,
            write_caps=write_caps)



@field_logic('control')
class ControlField(FieldLogic):
    def __init__(self, field_descriptor, dictionary):
        super().__init__(
            field_descriptor=field_descriptor,
            read_caps=AccessCapabilities(),
            write_caps=AccessCapabilities())

@field_logic('status')
class StatusField(FieldLogic):
    def __init__(self, field_descriptor, dictionary):
        super().__init__(
            field_descriptor=field_descriptor,
            read_caps=AccessCapabilities())
