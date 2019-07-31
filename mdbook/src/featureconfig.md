# Register file options

This configuration structure specifies some miscellaneous options that
affect the functionality and generation of the register file as a whole.

This structure supports the following configuration keys.

## `bus-width`

This key specifies the width of the generated AXI4-lite slave
bus.

The following values are supported:

 - `32` (default): the bus uses 32-bit data words.

 - `64`: the bus uses 64-bit data words.

This key is optional unless required by context. If not specified, the default value (`32`) is used.

## `max-outstanding`

This key specifies the maximum number of outstanding requests per
operation (read/write) for fields that support this. This value is
essentially the depth of a FIFO that stores the order in which
supporting fields were accessed. Since the width of the FIFO is the
2log of the number of supporting fields, the depth configuration has
very little effect if there is only one such field (everything but the
FIFO control logic will be optimized away) and no effect if there is
no such field.

The following values are supported:

 - `16` (default): there can be up to 16 outstanding requests.

 - an integer above or equal to 2: there can be up to this many outstanding requests.

This key is optional unless required by context. If not specified, the default value (`16`) is used.

## `insecure`

This key allows you to disable the multi-word register protection
features normally inferred by `vhdmmio` when any of the fields in the
register file are sensitive to `aw_prot` or `ar_prot`. This may save
some area. More information about `vhdmmio`'s security features is
available [here](permissionconfig.md).

The value must be a boolean (default `no`).

This key is optional unless required by context. If not specified, the default value (`no`) is used.

## `optimize`

Normally, `vhdmmio` infers address comparators that match *all* word
address bits in the incoming request to the field bitranges, such that
decode errors are properly generated. This can be quite costly in terms
of area and timing however, since in the worst case each register will
get its own 30-bit address comparator. Setting this flag to `yes`
allows `vhdmmio` to assign undefined behavior to unused addresses,
which lets it minimize the width of these comparators.

The value must be a boolean (default `no`).

This key is optional unless required by context. If not specified, the default value (`no`) is used.