# `flag` behavior

Fields with `flag' behavior behave like most edge/event-sensitive
interrupt flags in commercial peripherals work: occurance of the event
sets the flag bit, and writing a one to the bit through MMIO clears it
again.

Usually many of these flags are combined into a single register. Canonical
usage by software is then to read the register to determine which events
have occurred, write the read value back to the register, and then handle
the events. If a new event occurs between the read and write, its flag
will not be cleared, because a zero will be written to it by the write
action. This event will then be handled the next time the software reads
the flag register.

It isn't possible to detect how many events have occurred for a single
flag, just that there was at least one occurrance since the last read of
the flag. If this information is necessary, the `counter` behavior can be
used instead.

This structure supports the following configuration keys.

## `hw-read`

Configure the existence and behavior of the hardware read port.

The following values are supported:

 - `disabled` (default): no read port is generated.

 - `simple`: only the data output is generated.

This key is optional unless required by context. If not specified, the default value (`disabled`) is used.

## `reset`

Configures the reset value.

The following values are supported:

 - `no` (default): the internal data register resets to 0, with the valid flag set.

 - `yes`: the internal data register resets to 1, with the valid flag set.

 - an integer: the internal data register resets to the given value, with the valid flag set.

 - `generic`: the reset value is controlled through a VHDL generic.

This key is optional unless required by context. If not specified, the default value (`no`) is used.