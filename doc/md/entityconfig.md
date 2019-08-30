# VHDL entity configuration

This configuration structure can be used to configure the common
interfaces of the generated entity, such as the bus and the clock.

This structure supports the following configuration keys.

## `clock-name`

This key specifies the name of the clock input port. The clock is
always rising-edge-sensitive.

The value must be a string matching `[a-zA-Z][a-zA-Z0-9_]*` (default `clk`): name of the clock input port.

This key is optional unless required by context. If not specified, the default value (`clk`) is used.

## `reset-name`

This key specifies the name of the reset input port. The reset input
is always synchronous, but can be set to either active-high or
active-low using the `reset-active` parameter. The default `reset` name
can only be used when the reset is active-high due to limitations in
the template; it is suggested to suffix an `n` when the reset signal is
active-low to avoid this problem.

The value must be a string matching `[a-zA-Z][a-zA-Z0-9_]*` (default `reset`): name of the reset input port.

This key is optional unless required by context. If not specified, the default value (`reset`) is used.

## `reset-active`

This key specifies for which signal level the reset signal is
considered to be asserted.

The following values are supported:

 - `high` (default): the reset signal is active-high.

 - `low`: the reset signal is active-low. The default `reset` port name cannot be used.

This key is optional unless required by context. If not specified, the default value (`high`) is used.

## `bus-prefix`

This key specifies the prefix used for the AXI4-lite bus signals,
including underscore separator if one is desired. When the bus is not
flattened, the signals `<prefix>i` and `<prefix>o` are generated. When
flattened, the standard names for the AXI4-lite interface channels are
suffixed:

 - Write address channel: `awvalid`, `awready`, `awaddr` and `awprot`;
 - Write data channel: `wvalid`, `wready`, `wdata`, and `wstrb`;
 - Write response channel: `bvalid`, `bready`, and `bresp`;
 - Read address channel: `arvalid`, `arready`, `araddr`, and `arprot`;
 - Read data channel: `rvalid`, `rready`, `rdata`, and `rresp`.

The value must be a string matching `[a-zA-Z][a-zA-Z0-9_]*` (default `bus_`): prefix for the bus ports.

This key is optional unless required by context. If not specified, the default value (`bus_`) is used.

## `bus-flatten`

This key specifies whether records or flattened signals are desired
for the bus interface.

The following values are supported:

 - `no` (default): the bus is not flattened; the records from `vhdmmio_pkg.vhd` are used.

 - `yes`: the bus is flattened; the standard AXI4-lite signal names are used.

This key is optional unless required by context. If not specified, the default value (`no`) is used.