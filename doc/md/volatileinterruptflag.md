# `volatile-interrupt-flag` behavior

This field behavior works much like a regular `volatile-flag` field, but
operates on the interrupt pending flag of the associated interrupt instead
of a field-specific register. The read value of the field is one if and
only if the interrupt is pending, and the act of reading the field clears
the interrupt pending status. Since the interrupt flag can be cleared, the
associated interrupt implicitly becomes strobe-sensitive.

The arrayness of the interrupt must match the repetition/arrayness of the
field descriptor. The individual fields must be scalar.

This structure supports the following configuration key.

## `interrupt`

The name of the interrupt or interrupt array that this field is
associated with.

This key is required.