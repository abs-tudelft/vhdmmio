# `strobe` behavior

This behavior may be used to signal a request to hardware, for hardware
that can always handle the request immediately. When a 1 is written to a
bit in this register, the respective output bit is strobed high for one
cycle. Zero writes are ignored.

This structure does not support any configuration keys.