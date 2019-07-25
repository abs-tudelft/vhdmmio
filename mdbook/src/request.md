# `request` behavior

This behavior can be seen as both the inverse of a `flag` and as an
extension of `strobe`: the bits in the field are set by software writing
a one to them, and cleared when acknowledged by hardware. They can be used
for requests that cannot be handled immediately. By default, software can
use an MMIO read to determine whether a command has been acknowledged yet,
but this can be disabled to make the field write-only.

This structure supports the following configuration keys.

## `bus-read`

Configures what happens when a bus read occurs.

The following values are supported:

 - `enabled` (default): normal read access to field, ignoring valid bit.

 - `error`: reads always return a slave error.

 - `disabled`: read access is disabled.

This key is optional unless required by context. If not specified, the default value (`enabled`) is used.

## `reset`

Configures the reset value.

The following values are supported:

 - `no` (default): the internal data register resets to 0, with the valid flag set.

 - `yes`: the internal data register resets to 1, with the valid flag set.

 - an integer: the internal data register resets to the given value, with the valid flag set.

 - `generic`: the reset value is controlled through a VHDL generic.

This key is optional unless required by context. If not specified, the default value (`no`) is used.

## `ctrl-clear`

Controls the existence of the `ctrl_clear` control input
signal. When this signal is asserted, the internal data register is
cleared. The valid flag is not affected.

The value must be a boolean (default `no`).

This key is optional unless required by context. If not specified, the default value (`no`) is used.

## `ctrl-reset`

Controls the existence of the `ctrl_reset` control input
signal. When this signal is asserted, the field is reset, as if the
register file `reset` input were asserted.

The value must be a boolean (default `no`).

This key is optional unless required by context. If not specified, the default value (`no`) is used.

## `ctrl-bit-clear`

Controls the existence of the `ctrl_bit_clear` control input
signal. This signal is as wide as the field is. When a bit in this
input is high, the respective data bit is cleared.

The value must be a boolean (default `yes`).

This key is optional unless required by context. If not specified, the default value (`yes`) is used.

## `bit-overflow-internal`

Configures strobing an internal signal when a bit-set operation to
a bit that was already set occurs. This essentially serves as an
overflow signal for flag fields.

The following values are supported:

 - `null` (default): the feature is disabled.

 - a string matching `[a-zA-Z][a-zA-Z0-9_]*`: an internal signal with the given name is created (if necessary) and strobed when a bit-set operation occurs to an already-set bit.

This key is optional unless required by context. If not specified, the default value (`null`) is used.

## `bit-underflow-internal`

Configures strobing an internal signal when a bit-clear operation to
a bit that was already cleared occurs. This essentially serves as an
underflow signal for flag fields.

The following values are supported:

 - `null` (default): the feature is disabled.

 - a string matching `[a-zA-Z][a-zA-Z0-9_]*`: an internal signal with the given name is created (if necessary) and strobed when a bit-clear operation occurs to an already-cleared bit.

This key is optional unless required by context. If not specified, the default value (`null`) is used.