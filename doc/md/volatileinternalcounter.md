# `volatile-internal-counter` behavior

This field behaves like `volatile-counter`, but instead of the counter
being incremented by an external signal, it is incremented by an internal
signal.

This structure supports the following configuration keys.

## `hw-read`

Configure the existence and behavior of the hardware read port.

The following values are supported:

 - `disabled` (default): no read port is generated.

 - `simple`: only the data output is generated.

This key is optional unless required by context. If not specified, the default value (`disabled`) is used.

## `hw-write`

Configure the existence and behavior of the hardware write port.

The following values are supported:

 - `disabled` (default): no write port is generated.

 - `enabled`: a record consisting of a write enable flag and data is generated.

 - `accumulate`: like enabled, but the data is accumulated instead of written.

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

## `ctrl-increment`

Controls the existence of the `ctrl_increment` control input
signal. When this signal is asserted, the internal data register is
incremented.

The value must be a boolean (default `yes`).

This key is optional unless required by context. If not specified, the default value (`yes`) is used.

## `ctrl-decrement`

Controls the existence of the `ctrl_decrement` control input
signal. When this signal is asserted, the internal data register is
decremented.

The value must be a boolean (default `no`).

This key is optional unless required by context. If not specified, the default value (`no`) is used.

## `overflow-internal`

Configures strobing an internal signal when the most significant bit
of the internal register flips from high to low during an increment or
accumulate operation. This essentially serves as an overflow signal for
counter fields.

The following values are supported:

 - `null` (default): the feature is disabled.

 - a string matching `[a-zA-Z][a-zA-Z0-9_]*`: an internal signal with the given name is created (if necessary) and strobed when an increment or accumulate operation causes the MSB of the data register to be cleared.

This key is optional unless required by context. If not specified, the default value (`null`) is used.

## `underflow-internal`

Configures strobing an internal signal when the most significant bit
of the internal register flips from low to high during a decrement or
subtract operation. This essentially serves as an underflow signal for
counter fields.

The following values are supported:

 - `null` (default): the feature is disabled.

 - a string matching `[a-zA-Z][a-zA-Z0-9_]*`: an internal signal with the given name is created (if necessary) and strobed when a decrement or subtract operation causes the MSB of the data register to be set.

This key is optional unless required by context. If not specified, the default value (`null`) is used.

## `internal`

Configures the internal signal that is to be monitored. The value
must be a string matching `[a-zA-Z][a-zA-Z0-9_]*`.

This key is required.