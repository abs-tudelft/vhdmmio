# `interrupt-unmask` behavior

This field behavior allows software to access the unmask register
for the associated interrupt. A pending interrupt only asserts the outgoing
interrupt flag signal when it is unmasked. If there is no way to unmask an
interrupt, it resets to the unmasked state; otherwise it resets to masked.

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

 - `disabled`: write access is disabled.

 - `enabled` (default): write access is enabled.

 - `clear`: write access is enabled, and writing a one clears the associated flag.

 - `set`: write access is enabled, and writing a one sets the associated flag.

This key is optional unless required by context. If not specified, the default value (`enabled`) is used.