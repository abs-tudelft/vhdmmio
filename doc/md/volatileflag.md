# `volatile-flag` behavior

This behavior is similar to `flag`, but the flags are immediately
cleared when the field is read. The field is therefore read-only, allowing
write-only registers to reside at the same address. The access procedure
is also slightly faster, because no write action is required. However, the
required read-volatility makes it incompatible with processors/caches that
prefetch values; any infrastructure that may perform spurious reads may
inadvertantly clear the flags.

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

## `bit-overflow-internal`

Configures strobing an internal signal when a bit-set operation to
a bit that was already set occurs. This essentially serves as an
overflow signal for flag fields.

The following values are supported:

 - `null` (default): the feature is disabled.

 - a string matching `[a-zA-Z][a-zA-Z0-9_]*`: an internal signal with the given name is created (if necessary) and strobed when a bit-set operation occurs to an already-set bit.

This key is optional unless required by context. If not specified, the default value (`null`) is used.