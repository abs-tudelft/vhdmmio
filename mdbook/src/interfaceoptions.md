# VHDL interface options

Each field and interrupt in `vhdmmio` can register scalar and vector
inputs and outputs, as well as generics. This configuration structure
determines how these interfaces are exposed in the entity.

By default, the ports are grouped by field/interrupt into records while
generics are flattened, but either can be overridden. It is also possible
to group multiple fields/interrupts together in a single record.

This structure supports the following configuration keys.

## `group`

Name of the group record used for ports, if any. The ports for any
objects that share the same non-null `group` tag are combined into a
single record pair (`in` and `out`).

The following values are supported:

 - `null` (default): ports are not grouped in an additional record.

 - a string matching `[a-zA-Z][a-zA-Z0-9_]*`: ports are grouped in a record with the specified name.

This key is optional unless required by context. If not specified, the default value (`null`) is used.

## `flatten`

Whether the ports for this object should be flattened or combined in
a record (pair).

The following values are supported:

 - `no` (default): all ports needed for this object are combined in a record specific to the object. If `group` is specified in addition, there will be two levels of records. For arrays, an array of records is created.

 - `record`: The record mentioned above is flattened out. For array objects, `std_logic` ports become `std_logic_array`s (ascending range), and `std_logic_vector` ports become an array (ascending range) of an appropriately sized `std_logic_vector`.

 - `yes`: All port types are flattened to `std_logic`s or `std_logic_vector`s. `std_logic_vector` ports for array objects are simply concatenated using the customary descending range, with the lowest-indexed field in the least-significant position.

This key is optional unless required by context. If not specified, the default value (`no`) is used.

## `generic-group`

Same as `group`, but for generics.

The following values are supported:

 - `null` (default): generics are not grouped in an additional record.

 - a string matching `[a-zA-Z][a-zA-Z0-9_]*`: generics are grouped in a record with the specified name.

This key is optional unless required by context. If not specified, the default value (`null`) is used.

## `generic-flatten`

Same as `flatten`, but for generics.

The following values are supported:

 - `record` (default): generics are not grouped in a record, but arrays remain regular arrays (possibly of `std_logic_vector`s).

 - `yes`: as above, but all `std_logic`-based generics are flattened to single `std_logic`s or std_logic_vector`s. Other primitive types still receive their own custom array type for array objects.

 - `no`: all generics needed for this object are combined in a record specific to the object.

This key is optional unless required by context. If not specified, the default value (`record`) is used.