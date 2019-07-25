# `stream-to-mmio` behavior

Fields with `stream-to-mmio` behavior interface with an incoming AXI4
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
back and forth between systems.

This structure supports the following configuration keys.

## `bus-read`

Configures what happens when a bus read occurs.

The following values are supported:

 - `enabled` (default): reads from an empty holding register return 0.

 - `valid-only`: reads from an empty holding register return a slave error.

 - `valid-wait`: reads from an empty holding register are blocked until data is received from the stream.

This key is optional unless required by context. If not specified, the default value (`enabled`) is used.

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

## `underrun-internal`

Configures strobing an internal signal when a bus read occurs while
the stored value is invalid. This is equivalent to an underflow
condition for stream to MMIO fields. It is intended to be used for
underflow interrupts.

The following values are supported:

 - `null` (default): the feature is disabled.

 - a string matching `[a-zA-Z][a-zA-Z0-9_]*`: an internal signal with the given name is created (if necessary) and strobed when a bus read occurs while the internal valid signal is cleared.

This key is optional unless required by context. If not specified, the default value (`null`) is used.