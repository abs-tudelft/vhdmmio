# Interfaces for `custom` field behavior

Custom fields can specify any interfaces and state variables they want
to use through this configuration structure. The interface type is
determined based on which of the `input`, `output`, `generic`, `drive`,
`strobe`, `monitor`, and `state` keys is present to reduce verbosity in the
configuration files; exactly *one* of these must therefore be specified.

This structure supports the following configuration keys.

## `input`

Use this key to request an input signal to be generated.

The following values are supported:

 - `null` (default): this interface does not specify an input port.

 - a string matching `[a-zA-Za-z][a-zA-Z0-9_]*`: a scalar input port with the specified name is generated. The VHDL identifier for it is made available to the templates through `$s.<name>$`.

 - a string matching `[a-zA-Za-z][a-zA-Z0-9_]*:[0-9]+`: as above, but the port is a vector of the specified width.

This key is optional unless required by context. If not specified, the default value (`null`) is used.

## `output`

Use this key to request an output signal to be generated.

The following values are supported:

 - `null` (default): this interface does not specify an output port.

 - a string matching `[a-zA-Za-z][a-zA-Z0-9_]*`: a scalar output port with the specified name is generated. The VHDL identifier for it is made available to the templates through `$s.<name>$`.

 - a string matching `[a-zA-Za-z][a-zA-Z0-9_]*:[0-9]+`: as above, but the port is a vector of the specified width.

This key is optional unless required by context. If not specified, the default value (`null`) is used.

## `generic`

Use this key to request a generic to be generated.

The following values are supported:

 - `null` (default): this interface does not specify a generic.

 - a string matching `[a-zA-Za-z][a-zA-Z0-9_]*`: a scalar generic with the specified name is generated. The VHDL identifier for it is made available to the templates through `$s.<name>$`.

 - a string matching `[a-zA-Za-z][a-zA-Z0-9_]*:[0-9]+`: as above, but the generic is a vector of the specified width.

This key is optional unless required by context. If not specified, the default value (`null`) is used.

## `drive`

Use this key to request an internal signal driven by this field to
be generated.

The following values are supported:

 - `null` (default): this interface does not specify a driven internal.

 - a string matching `[a-zA-Za-z][a-zA-Z0-9_]*`: an internal with the specified name is generated and expected to be driven by this field. If the field is not repeated, the signal is scalar, otherwise its width equals the field repetition. The VHDL identifier for it is made available to the templates through `$s.<name>$`; it always behaves like an `std_logic`.

 - a string matching `[a-zA-Za-z][a-zA-Z0-9_]*:[0-9]+`: as above, but the internal signal is a vector of the specified width. This prevents field repetition from being used.

This key is optional unless required by context. If not specified, the default value (`null`) is used.

## `strobe`

Use this key to request an internal signal strobed by this field to
be generated. A strobed internal should only ever be or'd or written
high!

The following values are supported:

 - `null` (default): this interface does not specify a strobed internal.

 - a string matching `[a-zA-Za-z][a-zA-Z0-9_]*`: an internal with the specified name is generated and expected to be strobed by this field. If the field is not repeated, the signal is scalar, otherwise its width equals the field repetition. The VHDL identifier for it is made available to the templates through `$s.<name>$`; it always behaves like an `std_logic`.

 - a string matching `[a-zA-Za-z][a-zA-Z0-9_]*:[0-9]+`: as above, but the internal signal is a vector of the specified width. This prevents field repetition from being used.

This key is optional unless required by context. If not specified, the default value (`null`) is used.

## `monitor`

Use this key to request an internal signal monitored by this field
to be generated.

The following values are supported:

 - `null` (default): this interface does not specify a monitored internal.

 - a string matching `[a-zA-Za-z][a-zA-Z0-9_]*`: an internal with the specified name is generated and expected to only be read by this field. If the field is not repeated, the signal is scalar, otherwise its width equals the field repetition. The VHDL identifier for it is made available to the templates through `$s.<name>$`; it always behaves like an `std_logic`.

 - a string matching `[a-zA-Za-z][a-zA-Z0-9_]*:[0-9]+`: as above, but the internal signal is a vector of the specified width. This prevents field repetition from being used.

This key is optional unless required by context. If not specified, the default value (`null`) is used.

## `state`

Use this key to request a state variable to be generated.

The following values are supported:

 - `null` (default): this interface does not specify a state variable.

 - a string matching `[a-zA-Za-z][a-zA-Z0-9_]*`: a scalar state variable with the specified name is generated. The VHDL identifier for it is made available to the templates through `$s.<name>$`.

 - a string matching `[a-zA-Za-z][a-zA-Z0-9_]*:[0-9]+`: as above, but the state variable is a vector of the specified width.

This key is optional unless required by context. If not specified, the default value (`null`) is used.

## `type`

This key specifies the type of the signal. Note that only generics
support `natural` and `boolean` types, and only input and output ports
support the `axi4l-*-*` types.

The following values are supported:

 - `std_logic` (default): this interface is an `std_logic` or `std_logic_vector`.

 - `natural`: this interface is a VHDL `natural`.

 - `boolean`: this interface is a VHDL `boolean`.

 - `axi4l-req-32`: this interface is a 32-bit AXI4-lite request structure.

 - `axi4l-req-64`: this interface is a 64-bit AXI4-lite request structure.

 - `axi4l-resp-32`: this interface is a 32-bit AXI4-lite response structure.

 - `axi4l-resp-64`: this interface is a 64-bit AXI4-lite response structure.

This key is optional unless required by context. If not specified, the default value (`std_logic`) is used.