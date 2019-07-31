# Subaddress components

`vhdmmio` fields can encompass more than one address. This allows fields
such as memories and AXI passthrough to exist. Accessing such a field
involves an address in addition to the read and write data. This address is
called a subaddress. This configuration structure specifies part of a
custom subaddress format.

Note that exactly one of the `address`, `internal`, `input`, and `blank`
keys must be specified.

This structure supports the following configuration keys.

## `address`

This key specifies that this component of the subaddress is based on
bits taken from the incoming address. Normally these bits would be
masked out, but this is not required.

The following values are supported:

 - `null` (default): this subaddress component is not based on the incoming address.

 - an integer between 0 and 31: the specified bit of the incoming address is used.

 - `<high>..<low>`: the specified bitrange of the incoming address is used. The range is inclusive, so the number of bits in the subaddress component is `<high>` - `<low>` + 1.

This key is optional unless required by context. If not specified, the default value (`null`) is used.

## `internal`

This key specifies that this component of the subaddress is based
on the value of an internal signal.

The following values are supported:

 - `null` (default): this subaddress component is not based on an internal signal.

 - a string matching `[a-zA-Za-z][a-zA-Z0-9_]*`: a scalar internal with the given name is inserted into the subaddress at the current position.

 - a string matching `[a-zA-Za-z][a-zA-Z0-9_]*:[0-9]+`: a vector internal with the given name and width is inserted into the subaddress at the current position.

This key is optional unless required by context. If not specified, the default value (`null`) is used.

## `input`

This key specifies that this component of the subaddress is based
on the value of an external input signal.

The following values are supported:

 - `null` (default): this subaddress component is not based on an external input signal.

 - a string matching `[a-zA-Za-z][a-zA-Z0-9_]*`: a scalar external input signal with the given name is inserted into the subaddress at the current position.

 - a string matching `[a-zA-Za-z][a-zA-Z0-9_]*:[0-9]+`: a vector external input signal with the given name and width is inserted into the subaddress at the current position.

This key is optional unless required by context. If not specified, the default value (`null`) is used.

## `blank`

This key specifies that a number of blank bits should be inserted as
the next component. The bits are always zero; use the
`subaddress-offset` key in the field descriptor to set a different
value.

The following values are supported:

 - `null` (default): this subaddress component is not a blank.

 - an integer above or equal to 1: the specified number of blank (zero) bits are inserted.

This key is optional unless required by context. If not specified, the default value (`null`) is used.

## `slice`

For component based on vector signals (`internal` and `input`), this
key allows you to use only a subset of the signal for this component.
In conjunction with other subaddress components based on the same
signal, this allows bits to be reordered.

The following values are supported:

 - `null` (default): the entire vector is used.

 - an integer above or equal to 0: only the specified bit within the vector is used.

 - `<high>..<low>`: the specified subset of the vector is used. The range is inclusive, so the number of bits in the subaddress component is `<high>` - `<low>` + 1.

This key is optional unless required by context. If not specified, the default value (`null`) is used.