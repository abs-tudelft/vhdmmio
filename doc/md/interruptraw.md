# `interrupt-raw` behavior

This read-only field behavior reflects the state of the raw incoming
interrupt signal, regardless of whether the interrupt is enabled or whether
the flag is set.

The arrayness of the interrupt must match the repetition/arrayness of the
field descriptor. The individual fields must be scalar.

This structure supports the following configuration key.

## `interrupt`

The name of the interrupt or interrupt array that this field is
associated with.

This key is required.