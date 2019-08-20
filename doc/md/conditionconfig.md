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
condition.

The following values are supported:

 - a string matching `[a-zA-Za-z][a-zA-Z0-9_]*`: a scalar internal with the given name is used for the match condition.

 - a string matching `[a-zA-Za-z][a-zA-Z0-9_]*:[0-9]+`: a vector internal with the given name and width is used for the match condition.

This key is required.

## `value`

This key specifies the value that the signal must have for the
logical register to be addressed.

The following values are supported:

 - `no` (default): the signal value needs to be 0.

 - `yes`: the signal value needs to be 1.

 - an integer above or equal to 0: the signal needs to have the specified value.

 - a hex/bin integer with don't cares: the signal value is matched against the given number, specified as a string representation of a hexadecimal or binary integer which may contain don't cares (`-`). In hexadecimal integers, bit-granular don't-cares can be specified by inserting four-bit binary blocks enclosed in square braces in place of a hex digit.

 - `<address>/<size>`: as before, but the given number of LSBs are ignored in addition.

 - `<address>|<ignore>`: specifies the required signal value and ignored bits using two integers. Both integers can be specified in hexadecimal, binary, or decimal. A bit which is set in the `<ignore>` value is ignored in the matching process.

 - `<address>&<mask>`: specifies the required signal value and bitmask using two integers. Both integers can be specified in hexadecimal, binary, or decimal. A bit which is not set in the `<ignore>` value is ignored in the matching process.

This key is optional unless required by context. If not specified, the default value (`no`) is used.