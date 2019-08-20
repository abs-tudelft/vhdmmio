# `interrupt` behavior

This is the base class for the behavior of interrupt fields, i.e. fields
that operate on `vhdmmio`'s built-in interrupt system. They are associated
with an interrupt defined in the `interrupts` key of the register file
description. The arrayness of the interrupt must match the
repetition/arrayness of the field descriptor, and the individual fields
must be scalar.

This structure supports the following configuration keys.

## `interrupt`

The name of the interrupt or interrupt array that this field is
associated with.

This key is required.

## `mode`

The role that this field assumes for the associated interrupt.

The following values are supported:

 - `raw` (default): this field monitors the raw incoming interrupt request.

 - `enable`: this field monitors and/or controls the interrupt enable flag.

 - `flag`: this field monitors and/or controls the interrupt status flag.

 - `unmask`: this field monitors and/or controls the interrupt unmask flag.

 - `masked`: this field monitors the masked interrupt status flag.

This key is optional unless required by context. If not specified, the default value (`raw`) is used.

## `bus-read`

Configures what happens when a bus read occurs.

The following values are supported:

 - `disabled` (default): read access is disabled.

 - `enabled`: read access is enabled.

 - `clear`: read access is enabled, and reading clears the associated flag.

This key is optional unless required by context. If not specified, the default value (`disabled`) is used.

## `bus-write`

Configures what happens when a bus read occurs.

The following values are supported:

 - `disabled` (default): write access is disabled.

 - `enabled`: write access is enabled.

 - `clear`: write access is enabled, and writing a one clears the associated flag.

 - `set`: write access is enabled, and writing a one sets the associated flag.

This key is optional unless required by context. If not specified, the default value (`disabled`) is used.