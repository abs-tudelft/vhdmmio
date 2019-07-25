# `control` behavior

Fields with `control` behavior are used to push runtime configuration
values from software to hardware. They are normally read-write on the MMIO
bus and respect the AXI4L byte strobe bits so they can be easily (though
not necessarily atomically) updated partially, but read access can be
disabled and write access can be simplified if this is desirable.

The hardware interface by default consists of just an `std_logic` or
`std_logic_vector` with the current value of the field, but you can also
enable a valid bit by setting `hw-read` to `enabled` if you so desire.
You'll also need to set `bus-write` to `enabled` and `after-bus-write` to
`validate` to make that work as you would expect: the value will be marked
invalid from reset to when it's first written. You can also make the field
one-time-programmable by selecting `invalid` or `invalid-only` for
`bus-write` instead of `enabled`.

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

 - `invalid`: as above, but ignores the write when the register is valid.

 - `invalid-only`: as above, but fails when register is already valid.

This key is optional unless required by context. If not specified, the default value (`masked`) is used.

## `after-bus-write`

Configures what happens after a bus write.

The following values are supported:

 - `nothing` (default): no extra operation after write.

 - `validate`: register is validated after write.

This key is optional unless required by context. If not specified, the default value (`nothing`) is used.

## `hw-read`

Configure the existence and behavior of the hardware read port.

The following values are supported:

 - `simple` (default): only the data output is generated.

 - `enabled`: both a data and a valid output signal are generated.

This key is optional unless required by context. If not specified, the default value (`simple`) is used.

## `reset`

Configures the reset value.

The following values are supported:

 - `no`: the internal data register resets to 0, with the valid flag set.

 - `yes`: the internal data register resets to 1, with the valid flag set.

 - `null` (default): the internal data register resets to 0, with the valid flag cleared.

 - an integer: the internal data register resets to the given value, with the valid flag set.

 - `generic`: the reset value is controlled through a VHDL generic.

This key is optional unless required by context. If not specified, the default value (`null`) is used.

## `ctrl-lock`

Controls the existence of the `ctrl_lock` control input signal. When
this signal is asserted, writes are ignored.

The value must be a boolean (default `no`).

This key is optional unless required by context. If not specified, the default value (`no`) is used.

## `ctrl-invalidate`

Controls the existence of the `ctrl_invalidate` control input
signal. When this signal is asserted, the internal valid flag is
cleared. The data register is also set to 0.

The value must be a boolean (default `no`).

This key is optional unless required by context. If not specified, the default value (`no`) is used.

## `ctrl-reset`

Controls the existence of the `ctrl_reset` control input
signal. When this signal is asserted, the field is reset, as if the
register file `reset` input were asserted.

The value must be a boolean (default `no`).

This key is optional unless required by context. If not specified, the default value (`no`) is used.