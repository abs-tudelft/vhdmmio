# `interrupt-enable` behavior

This field behavior allows software to access the enable register
for the associated interrupt. Incoming interrupt requests only affect the
interrupt flag register when the enable register is set. If there is no
way to enable an interrupt, it resets to the enabled state; otherwise it
resets to disabled.

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