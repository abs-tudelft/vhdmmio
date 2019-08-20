# `interrupt-pend` behavior

This field behavior allows software to set pend interrupts manually by
writing a one, regardless of the enable flag or the incoming interrupt
request. Since the interrupt flag can be set, the associated interrupt
implicitly becomes strobe-sensitive, and needs a way to clear the flag as
well. This can be done by reading this field when `bus-read` is set to
`clear`, or through a (`volatile-`)`interrupt-flag` field.

The arrayness of the interrupt must match the repetition/arrayness of the
field descriptor. The individual fields must be scalar.

This structure supports the following configuration keys.

## `interrupt`

The name of the interrupt or interrupt array that this field is
associated with.

This key is required.

## `bus-read`

Configures what happens when a bus read occurs.

The following values are supported:

 - `disabled`: read access is disabled.

 - `enabled` (default): read access is enabled.

 - `clear`: read access is enabled, and reading clears the associated flag.

This key is optional unless required by context. If not specified, the default value (`enabled`) is used.