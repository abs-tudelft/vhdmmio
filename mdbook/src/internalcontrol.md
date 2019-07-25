# `internal-control` behavior

This field behaves like a control register that constrols an internal
signal by default. That is, the MMIO bus interface is read/write, and the
contents of the internal register drives an internal signal. The name of
the internal signal must be set using `drive-internal`.

This structure supports the following configuration keys.

## `bus-read`

Configures what happens when a bus read occurs.

The following values are supported:

 - `enabled` (default): normal read access to field, ignoring valid bit.

 - `error`: reads always return a slave error.

 - `disabled`: read access is disabled.

This key is optional unless required by context. If not specified, the default value (`enabled`) is used.

## `bus-write`

Configures what happens when a bus write occurs.

The following values are supported:

 - `masked` (default): write access respects strobe bits. Precludes after-bus-write.

 - `enabled`: normal write access to register. Masked bits are written 0.

This key is optional unless required by context. If not specified, the default value (`masked`) is used.

## `reset`

Configures the reset value.

The following values are supported:

 - `no` (default): the internal data register resets to 0, with the valid flag set.

 - `yes`: the internal data register resets to 1, with the valid flag set.

 - an integer: the internal data register resets to the given value, with the valid flag set.

 - `generic`: the reset value is controlled through a VHDL generic.

This key is optional unless required by context. If not specified, the default value (`no`) is used.

## `internal`

Configures the internal signal that is to be driven. The value
must be a string matching `[a-zA-Z][a-zA-Z0-9_]*`.

This key is required.