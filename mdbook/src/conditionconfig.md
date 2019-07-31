# Additional address match conditions

To support disabling registers at runtime and paged/indirect register
files, `vhdmmio` allows you to specify additional conditions for the
address matching logic of each register. This may be useful when not
enough address space is allocated to the register file to fit all the
registers, or when you want to emulate legacy register files such as a
16550 UART.

This structure supports the following configuration keys.

## `internal`

This key specifies the internal signal to use for the match
condition, if applicable. Either this key or `input` must be
specified.

The following values are supported:

 - `null` (default): no internal is specified, `input` must be specified instead.

 - a string matching `[a-zA-Za-z][a-zA-Z0-9_]*`: a scalar internal with the given name is used for the match condition.

 - a string matching `[a-zA-Za-z][a-zA-Z0-9_]*:[0-9]+`: a vector internal with the given name and width is used for the match condition.

This key is optional unless required by context. If not specified, the default value (`null`) is used.

## `input`

This key specifies the external input signal to use for the match
condition, if applicable. Either this key or `internal` must be
specified.

The following values are supported:

 - `null` (default): no external input is specified, `internal` must be specified instead.

 - a string matching `[a-zA-Za-z][a-zA-Z0-9_]*`: a scalar input signal with the given name is used for the match condition.

 - a string matching `[a-zA-Za-z][a-zA-Z0-9_]*:[0-9]+`: a vector input signal with the given name and width is used for the match condition.

This key is optional unless required by context. If not specified, the default value (`null`) is used.

## `value`

This key specifies the value that the signal must have for the
logical register to be addressed.

The following values are supported:

 - `no` (default): the signal value needs to be 0.

 - `yes`: the signal value needs to be 1.

 - an integer: the signal value needs to match the specified value.

This key is optional unless required by context. If not specified, the default value (`no`) is used.

## `ignore`

This key specifies the value that the signal must have for the
logical register to be addressed.

The following values are supported:

 - `0` (default): all bits must match.

 - a different integer: the bits set in this value are ignored when matching against `value`.

This key is optional unless required by context. If not specified, the default value (`0`) is used.