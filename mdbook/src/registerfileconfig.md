# Register files

This is the root configuration structure for `vhdmmio` register
files.

This structure supports the following configuration keys.

## `metadata`

This configuration structure is used to name and document the
register file.

This key must be set to a dictionary. Its structure is defined [here](metadataconfig.md). Not specifying the key is equivalent to specifying an empty dictionary.

## `features`

This configuration structure is used to specify some options that
affect register file as a whole.

This key must be set to a dictionary. Its structure is defined [here](featureconfig.md). Not specifying the key is equivalent to specifying an empty dictionary.

## `interface`

This key specifies the default VHDL entity interface generation
options for fields and interrupts alike.

This key must be set to a dictionary. Its structure is defined [here](interfaceconfig.md). Not specifying the key is equivalent to specifying an empty dictionary.

## `fields`

This key describes the fields that the register file contains.

This key must be set to a list of dictionaries, of which the structure is defined [here](fieldconfig.md). In addition, the `subfields` key can be used to define the list elements as a tree; if it is present in one of the dictionaries, the dictionary becomes a non-leaf node, with the `subfields` key specifying the list of child nodes. This tree is flattened during parsing, in such a way that the configuration for a flattened node becomes the root dictionary, updated with its child dictionary, all the way down to the leaf node; the non-leaf nodes essentially set the default values for their children. For example,

```
fields:
- a: 1
  b: 2
  c: 3
  subfields:
  - a: 5
  - d: 4
```

is equivalent to

```
fields:
- a: 5
  b: 2
  c: 3
- a: 1
  b: 2
  c: 3
  d: 4
```

This can be useful for specifying repetetive structures.

This key is optional. Not specifying it is equivalent to specifying an empty list.

## `interrupts`

This key describes the interrupts that the register file
contains.

This key must be set to a list of dictionaries, of which the structure is defined [here](interruptconfig.md).

This key is optional. Not specifying it is equivalent to specifying an empty list.