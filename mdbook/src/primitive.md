# `primitive` behavior

This is the base class for regular field behavior. It can be used for
everything from simple status/control fields to stream interfaces and
performance counters. Most behaviors simply derive from this by overriding
some parameters and changing defaults for others.

A primitive field has up to two internal registers associated with it. One
contains data, and is thus as wide as the field is; the other is a single
bit representing whether the data register is valid. How these registers
are initialized and used (if at all) depends entirely on the
configuration.

This structure supports the following configuration keys.

## `bus-read`

Configures what happens when a bus read occurs.

The following values are supported:

 - `disabled` (default): read access is disabled.

 - `error`: reads always return a slave error.

 - `enabled`: normal read access to field, ignoring valid bit.

 - `valid-wait`: as above, but blocks until field is valid.

 - `valid-only`: as above, but fails when field is not valid.

This key is optional unless required by context. If not specified, the default value (`disabled`) is used.

## `after-bus-read`

Configures what happens after a bus read.

The following values are supported:

 - `nothing` (default): no extra operation after read.

 - `invalidate`: field is invalidated and cleared after read.

 - `clear`: field is cleared after read, valid untouched.

 - `increment`: register is incremented after read, valid untouched.

 - `decrement`: register is decremented after read, valid untouched.

This key is optional unless required by context. If not specified, the default value (`nothing`) is used.

## `bus-write`

Configures what happens when a bus write occurs.

The following values are supported:

 - `disabled` (default): write access is disabled.

 - `error`: writes always return a slave error.

 - `enabled`: normal write access to register. Masked bits are written 0.

 - `invalid`: as above, but ignores the write when the register is valid.

 - `invalid-wait`: as above, but blocks until register is invalid.

 - `invalid-only`: as above, but fails when register is already valid.

 - `masked`: write access respects strobe bits. Precludes after-bus-write.

 - `accumulate`: write data is added to the register.

 - `subtract`: write data is subtracted from the register.

 - `bit-set`: bits that are written 1 are set in the register.

 - `bit-clear`: bits that are written 1 are cleared in the register.

 - `bit-toggle`: bits that are written 1 are toggled in the register.

This key is optional unless required by context. If not specified, the default value (`disabled`) is used.

## `after-bus-write`

Configures what happens after a bus write.

The following values are supported:

 - `nothing` (default): no extra operation after write.

 - `validate`: register is validated after write.

 - `invalidate`: as above, but invalidated again one cycle later.

This key is optional unless required by context. If not specified, the default value (`nothing`) is used.

## `hw-read`

Configure the existence and behavior of the hardware read port.

The following values are supported:

 - `disabled` (default): no read port is generated.

 - `simple`: only the data output is generated.

 - `enabled`: both a data and a valid output signal are generated.

 - `handshake`: a stream-to-mmio ready signal is generated.

This key is optional unless required by context. If not specified, the default value (`disabled`) is used.

## `hw-write`

Configure the existence and behavior of the hardware write port.

The following values are supported:

 - `disabled` (default): no write port is generated.

 - `status`: the register is constantly driven by a port and is always valid.

 - `enabled`: a record consisting of a write enable flag and data is generated.

 - `stream`: like enabled, but the write only occurs when the register is invalid.

 - `accumulate`: like enabled, but the data is accumulated instead of written.

 - `subtract`: like enabled, but the data is subtracted instead of written.

 - `set`: like enabled, but bits that are written 1 are set in the register.

 - `reset`: like enabled, but bits that are written 1 are cleared in the register.

 - `toggle`: like enabled, but bits that are written 1 are toggled in the register.

This key is optional unless required by context. If not specified, the default value (`disabled`) is used.

## `after-hw-write`

Configures what happens after a hardware write.

The following values are supported:

 - `nothing` (default): no extra operation after write.

 - `validate`: register is automatically validated after write.

This key is optional unless required by context. If not specified, the default value (`nothing`) is used.

## `reset`

Configures the reset value.

The following values are supported:

 - `no` (default): the internal data register resets to 0, with the valid flag set.

 - `yes`: the internal data register resets to 1, with the valid flag set.

 - `null`: the internal data register resets to 0, with the valid flag cleared.

 - an integer: the internal data register resets to the given value, with the valid flag set.

 - `generic`: the reset value is controlled through a VHDL generic.

This key is optional unless required by context. If not specified, the default value (`no`) is used.

## `ctrl-lock`

Controls the existence of the `ctrl_lock` control input signal. When
this signal is asserted, writes are ignored.

The value must be a boolean (default `no`).

This key is optional unless required by context. If not specified, the default value (`no`) is used.

## `ctrl-validate`

Controls the existence of the `ctrl_validate` control input signal.
When this signal is asserted, the internal valid flag is set.

The value must be a boolean (default `no`).

This key is optional unless required by context. If not specified, the default value (`no`) is used.

## `ctrl-invalidate`

Controls the existence of the `ctrl_invalidate` control input
signal. When this signal is asserted, the internal valid flag is
cleared. The data register is also set to 0.

The value must be a boolean (default `no`).

This key is optional unless required by context. If not specified, the default value (`no`) is used.

## `ctrl-ready`

Controls the existence of the `ctrl_ready` control input signal.
This signal behaves like an AXI stream ready signal for MMIO to stream
fields.

The value must be a boolean (default `no`).

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

The value must be a boolean (default `no`).

This key is optional unless required by context. If not specified, the default value (`no`) is used.

## `ctrl-decrement`

Controls the existence of the `ctrl_decrement` control input
signal. When this signal is asserted, the internal data register is
decremented.

The value must be a boolean (default `no`).

This key is optional unless required by context. If not specified, the default value (`no`) is used.

## `ctrl-bit-set`

Controls the existence of the `ctrl_bit_set` control input
signal. This signal is as wide as the field is. When a bit in this
input is high, the respective data bit is set.

The value must be a boolean (default `no`).

This key is optional unless required by context. If not specified, the default value (`no`) is used.

## `ctrl-bit-clear`

Controls the existence of the `ctrl_bit_clear` control input
signal. This signal is as wide as the field is. When a bit in this
input is high, the respective data bit is cleared.

The value must be a boolean (default `no`).

This key is optional unless required by context. If not specified, the default value (`no`) is used.

## `ctrl-bit-toggle`

Controls the existence of the `ctrl_bit_toggle` control input
signal. This signal is as wide as the field is. When a bit in this
input is high, the respective data bit is toggled.

The value must be a boolean (default `no`).

This key is optional unless required by context. If not specified, the default value (`no`) is used.

## `drive-internal`

Configures driving an internal signal with the internal data
register belonging to this field.

The following values are supported:

 - `null` (default): the feature is disabled.

 - a string matching `[a-zA-Z][a-zA-Z0-9_]*`: an internal signal with the given name is created and driven with the value in the internal data register for this field.

This key is optional unless required by context. If not specified, the default value (`null`) is used.

## `full-internal`

Configures driving an internal signal high when the internal data
register is valid. This essentially serves as a holding register full
signal for stream interface fields.

The following values are supported:

 - `null` (default): the feature is disabled.

 - a string matching `[a-zA-Z][a-zA-Z0-9_]*`: an internal signal with the given name is created (if necessary) and driven by the internal valid register of this field.

This key is optional unless required by context. If not specified, the default value (`null`) is used.

## `empty-internal`

Configures driving an internal signal high when the internal data
register is invalid. This essentially serves as a holding register
empty signal for stream interface fields.

The following values are supported:

 - `null` (default): the feature is disabled.

 - a string matching `[a-zA-Z][a-zA-Z0-9_]*`: an internal signal with the given name is created (if necessary) and driven by the one's complement of the internal valid register of this field.

This key is optional unless required by context. If not specified, the default value (`null`) is used.

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

## `bit-overflow-internal`

Configures strobing an internal signal when a bit-set operation to
a bit that was already set occurs. This essentially serves as an
overflow signal for flag fields.

The following values are supported:

 - `null` (default): the feature is disabled.

 - a string matching `[a-zA-Z][a-zA-Z0-9_]*`: an internal signal with the given name is created (if necessary) and strobed when a bit-set operation occurs to an already-set bit.

This key is optional unless required by context. If not specified, the default value (`null`) is used.

## `bit-underflow-internal`

Configures strobing an internal signal when a bit-clear operation to
a bit that was already cleared occurs. This essentially serves as an
underflow signal for flag fields.

The following values are supported:

 - `null` (default): the feature is disabled.

 - a string matching `[a-zA-Z][a-zA-Z0-9_]*`: an internal signal with the given name is created (if necessary) and strobed when a bit-clear operation occurs to an already-cleared bit.

This key is optional unless required by context. If not specified, the default value (`null`) is used.

## `overrun-internal`

Configures strobing an internal signal when a bus write occurs while
the stored value was already valid. This is equivalent to an overflow
condition for MMIO to stream fields. It is intended to be used for
overflow interrupts.

The following values are supported:

 - `null` (default): the feature is disabled.

 - a string matching `[a-zA-Z][a-zA-Z0-9_]*`: an internal signal with the given name is created (if necessary) and strobed when a bus write occurs while the internal valid signal is set.

This key is optional unless required by context. If not specified, the default value (`null`) is used.

## `underrun-internal`

Configures strobing an internal signal when a bus read occurs while
the stored value is invalid. This is equivalent to an underflow
condition for stream to MMIO fields. It is intended to be used for
underflow interrupts.

The following values are supported:

 - `null` (default): the feature is disabled.

 - a string matching `[a-zA-Z][a-zA-Z0-9_]*`: an internal signal with the given name is created (if necessary) and strobed when a bus read occurs while the internal valid signal is cleared.

This key is optional unless required by context. If not specified, the default value (`null`) is used.

## `monitor-internal`

Configures monitoring an internal signal with this field.

The following values are supported:

 - `null` (default): the feature is disabled.

 - a string matching `[a-zA-Z][a-zA-Z0-9_]*`: the field monitors the internal signal with the given name. `monitor-mode` determines how the signal is used.

This key is optional unless required by context. If not specified, the default value (`null`) is used.

## `monitor-mode`

Configures how `monitor-internal` works. If `monitor-internal` is
not specified, this key is no-op.

The following values are supported:

 - `status` (default): the internal data register is constantly assigned to the vector-sized internal signal named by `monitor-internal`.

 - `bit-set`: the internal data register is constantly or'd with the vector-sized internal signal named by `monitor-internal`.

 - `increment`: the internal data register is incremented whenever the respective bit in the repeat-sized internal signal named by `monitor-internal` is asserted.

This key is optional unless required by context. If not specified, the default value (`status`) is used.