# `interrupt-status` behavior

This read-only field behavior reflects the state of the interrupt flag
register masked by the interrupt mask register. It is one if and only if
the interrupt is pending and unmasked.

The arrayness of the interrupt must match the repetition/arrayness of the
field descriptor. The individual fields must be scalar.

This structure supports the following configuration key.

## `interrupt`

The name of the interrupt or interrupt array that this field is
associated with.

This key is required.