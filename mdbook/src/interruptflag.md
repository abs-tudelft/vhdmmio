# `interrupt-flag` behavior

This field behavior works much like a regular `flag` field, but operates
on the interrupt pending flag of the associated interrupt instead of a
field-specific register. The read value of the field is one if and only if
the interrupt is pending, regardless of mask. Writing a one to the field
clears the flag. If only one of these operations is needed, the other can
be disabled.

If the write mode of this field is enabled, the associated interrupt
implicitly becomes strobe-sensitive.

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

 - `enabled` (default): read access is enabled.

 - `disabled`: read access is disabled.

This key is optional unless required by context. If not specified, the default value (`enabled`) is used.

## `bus-write`

Configures what happens when a bus read occurs.

The following values are supported:

 - `clear` (default): write access is enabled, and writing a one clears the associated flag.

 - `disabled`: write access is disabled.

This key is optional unless required by context. If not specified, the default value (`clear`) is used.