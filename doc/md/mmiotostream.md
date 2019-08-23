# `mmio-to-stream` behavior

Fields with `mmio-to-stream` behavior interface with an outgoing AXI4
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
back and forth between systems.

This structure supports the following configuration keys.

## `bus-write`

Configures what happens when a bus write occurs.

The following values are supported:

 - `invalid` (default): writes to a full holding register are silently ignored.

 - `enabled`: writes to a full holding register override the register. NOTE: this is not AXI4-stream compliant behavior, since `data` must remain stable between validation and the completed handshake.

 - `invalid-wait`: writes to a full holding register are blocked until the register is popped by the stream.

 - `invalid-only`: writes to a full holding register return a slave error.

This key is optional unless required by context. If not specified, the default value (`invalid`) is used.

## `reset`

Configures the reset value.

The following values are supported:

 - `null` (default): the internal data register resets to 0, with the valid flag cleared.

 - `no`: the internal data register resets to 0, with the valid flag set.

 - `yes`: the internal data register resets to 1, with the valid flag set.

 - an integer: the internal data register resets to the given value, with the valid flag set.

 - `generic`: the reset value is controlled through a VHDL generic.

This key is optional unless required by context. If not specified, the default value (`null`) is used.

## `full-internal`

Configures driving an internal signal high when the internal data
register is valid. This essentially serves as a holding register full
signal for stream interface fields.

The following values are supported:

 - `null` (default): the feature is disabled.

 - a string matching `[a-zA-Z][a-zA-Z0-9_]*`: an internal signal with the given name is created (if necessary) and driven by the internal valid register of this field.

This key is optional unless required by context. If not specified, the default value (`null`) is used.

## `empty-internal`

Configures driving an internal signal high when the internal data
register is invalid. This essentially serves as a holding register
empty signal for stream interface fields.

The following values are supported:

 - `null` (default): the feature is disabled.

 - a string matching `[a-zA-Z][a-zA-Z0-9_]*`: an internal signal with the given name is created (if necessary) and driven by the one's complement of the internal valid register of this field.

This key is optional unless required by context. If not specified, the default value (`null`) is used.

## `overrun-internal`

Configures strobing an internal signal when a bus write occurs while
the stored value was already valid. This is equivalent to an overflow
condition for MMIO to stream fields. It is intended to be used for
overflow interrupts.

The following values are supported:

 - `null` (default): the feature is disabled.

 - a string matching `[a-zA-Z][a-zA-Z0-9_]*`: an internal signal with the given name is created (if necessary) and strobed when a bus write occurs while the internal valid signal is set.

This key is optional unless required by context. If not specified, the default value (`null`) is used.