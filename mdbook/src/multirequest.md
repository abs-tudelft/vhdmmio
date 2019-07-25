# `multi-request` behavior

`multi-request` fields accumulate anything written to them, and by
default allow hardware to decrement them. This may be used to request
a certain number of things with a single, atomic MMIO write.

This structure supports the following configuration keys.

## `bus-read`

Configures what happens when a bus read occurs.

The following values are supported:

 - `enabled` (default): normal read access to field, ignoring valid bit.

 - `error`: reads always return a slave error.

 - `disabled`: read access is disabled.

This key is optional unless required by context. If not specified, the default value (`enabled`) is used.

## `hw-write`

Configure the existence and behavior of the hardware write port.

The following values are supported:

 - `disabled` (default): no write port is generated.

 - `subtract`: like enabled, but the data is subtracted instead of written.

This key is optional unless required by context. If not specified, the default value (`disabled`) is used.

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

## `ctrl-decrement`

Controls the existence of the `ctrl_decrement` control input
signal. When this signal is asserted, the internal data register is
decremented.

The value must be a boolean (default `yes`).

This key is optional unless required by context. If not specified, the default value (`yes`) is used.