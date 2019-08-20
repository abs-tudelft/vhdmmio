# `internal-status` behavior

Fields with `internal-status` behavior always return the current state
if an internal signal.

This structure supports the following configuration key.

## `internal`

Configures the internal signal that is to be monitored. The value
must be a string matching `[a-zA-Z][a-zA-Z0-9_]*`.

This key is required.