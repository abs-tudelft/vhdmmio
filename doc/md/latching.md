# `latching` behavior

The `latching` behavior is a lot like `status`, but more advanced. It is
used when status information is not always available, but only updated
sporadically through a write enable. This means that there is an "invalid"
state of some kind, used before the first status value is received. By
default fields with this behavior will just read as 0 in this state, but
this behavior can be overridden with the options below. For instance, the
field can be configured to block the read access until the status is valid.
It's also possible to enable a control signal that invalidates the field on
demand, or to invalidate on read.

This structure supports the following configuration keys.

## `bus-read`

Configures what happens when a bus read occurs.

The following values are supported:

 - `enabled` (default): normal read access to field, ignoring valid bit.

 - `valid-wait`: as above, but blocks until field is valid.

 - `valid-only`: as above, but fails when field is not valid.

This key is optional unless required by context. If not specified, the default value (`enabled`) is used.

## `after-bus-read`

Configures what happens after a bus read.

The following values are supported:

 - `nothing` (default): no extra operation after read.

 - `invalidate`: field is invalidated and cleared after read.

 - `clear`: field is cleared after read, valid untouched.

This key is optional unless required by context. If not specified, the default value (`nothing`) is used.

## `after-hw-write`

Configures what happens after a hardware write.

The following values are supported:

 - `nothing` (default): no extra operation after write.

 - `validate`: register is automatically validated after write.

This key is optional unless required by context. If not specified, the default value (`nothing`) is used.

## `reset`

Configures the reset value.

The following values are supported:

 - `no`: the internal data register resets to 0, with the valid flag set.

 - `yes`: the internal data register resets to 1, with the valid flag set.

 - `null` (default): the internal data register resets to 0, with the valid flag cleared.

 - an integer: the internal data register resets to the given value, with the valid flag set.

 - `generic`: the reset value is controlled through a VHDL generic.

This key is optional unless required by context. If not specified, the default value (`null`) is used.

## `ctrl-validate`

Controls the existence of the `ctrl_validate` control input signal.
When this signal is asserted, the internal valid flag is set.

The value must be a boolean (default `no`).

This key is optional unless required by context. If not specified, the default value (`no`) is used.

## `ctrl-invalidate`

Controls the existence of the `ctrl_invalidate` control input
signal. When this signal is asserted, the internal valid flag is
cleared. The data register is also set to 0.

The value must be a boolean (default `no`).

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

## `ctrl-increment`

Controls the existence of the `ctrl_increment` control input
signal. When this signal is asserted, the internal data register is
incremented.

The value must be a boolean (default `no`).

This key is optional unless required by context. If not specified, the default value (`no`) is used.

## `ctrl-decrement`

Controls the existence of the `ctrl_decrement` control input
signal. When this signal is asserted, the internal data register is
decremented.

The value must be a boolean (default `no`).

This key is optional unless required by context. If not specified, the default value (`no`) is used.

## `ctrl-bit-set`

Controls the existence of the `ctrl_bit_set` control input
signal. This signal is as wide as the field is. When a bit in this
input is high, the respective data bit is set.

The value must be a boolean (default `no`).

This key is optional unless required by context. If not specified, the default value (`no`) is used.

## `ctrl-bit-clear`

Controls the existence of the `ctrl_bit_clear` control input
signal. This signal is as wide as the field is. When a bit in this
input is high, the respective data bit is cleared.

The value must be a boolean (default `no`).

This key is optional unless required by context. If not specified, the default value (`no`) is used.

## `ctrl-bit-toggle`

Controls the existence of the `ctrl_bit_toggle` control input
signal. This signal is as wide as the field is. When a bit in this
input is high, the respective data bit is toggled.

The value must be a boolean (default `no`).

This key is optional unless required by context. If not specified, the default value (`no`) is used.