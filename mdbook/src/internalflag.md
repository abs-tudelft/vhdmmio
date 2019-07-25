# `internal-flag` behavior

`internal-flag` fields behave like `flag` fields, but instead of the
flags being set by an external signal, it is set by an internal signal.
This may for instance be used in conjunction with the overrun output of an
MMIO to stream field.

This structure supports the following configuration keys.

## `hw-read`

Configure the existence and behavior of the hardware read port.

The following values are supported:

 - `disabled` (default): no read port is generated.

 - `simple`: only the data output is generated.

This key is optional unless required by context. If not specified, the default value (`disabled`) is used.

## `reset`

Configures the reset value.

The following values are supported:

 - `no` (default): the internal data register resets to 0, with the valid flag set.

 - `yes`: the internal data register resets to 1, with the valid flag set.

 - an integer: the internal data register resets to the given value, with the valid flag set.

 - `generic`: the reset value is controlled through a VHDL generic.

This key is optional unless required by context. If not specified, the default value (`no`) is used.

## `internal`

Configures the internal signal that is to be monitored. The value
must be a string matching `[a-zA-Z][a-zA-Z0-9_]*`.

This key is required.