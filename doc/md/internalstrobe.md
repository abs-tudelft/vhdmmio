# `internal-strobe` behavior

This behavior may be used to signal a request to another `vhdmmio`
entity, such as a counter field. When a 1 is written to a bit in this
register, the respective bit in the internal signal is strobed high for one
cycle. Zero writes are ignored.

This structure supports the following configuration key.

## `internal`

Configures the internal signal that is to be driven. The value
must be a string matching `[a-zA-Z][a-zA-Z0-9_]*`.

This key is required.