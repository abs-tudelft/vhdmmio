# Metadata

This configuration structure is used to identify and document objects
within `vhdmmio`.

This structure supports the following configuration keys.

## `mnemonic`

The mnemonic of the object. Mnemonics are usually very short,
uppercase identifiers, idiomatically used within register file
descriptions. `vhdmmio` requires that they are unique within the
current context only; that is, two fields in a single logical
register cannot have the same mnemonic, but if they were in different
logical registers this would be fine. However, chains of mnemonics
separated by underscores must still be unique. For instance, it's
illegal to have a register `X` containing field `Y_Z` and another
register `X_Y` containing field `Z`.

If the mnemonic names an array, it cannot end in a number, since the
array index is added to the mnemonic in various contexts.

If no mnemonic is specified, it is generated from the name by simply
uppercasing it. Either name, mnemonic, or both must be specified.

This key is optional unless required by context.

## `name`

The name of the object. Names are generally longer and more
descriptive than mnemonics, but also need to be more unique; no two
fields within a register file can have the same name. Matching is
case-insensitive since VHDL is case-insensitive, but `vhdmmio` never
changes the case of a name.

Like mnemonics, if the name names an array, it cannot end in a number,
since the array index is added to the name in various contexts.

If no name is specified, it is generated from the mnemonic by simply
lowercasing it. Either name, mnemonic, or both must be specified.

This key is optional unless required by context.

## `brief`

A brief, one-line description of the object. This will be rendered
as markdown in the documentation output. Idiomatically, the brief
description should start with a lowercase letter and end in a period,
so it looks good when used in a list like `"<name>: <brief>"`. The
brief may also be used as a standalone sentence; in this case, the
first letter is automatically uppercased. When printed in source code
comments, the description is automatically wrapped to an appropriate
line length. All spacing characters, including newlines, are collapsed
into a single space before the brief is used.

Brief documentation may be printed once for an array of fields or for
each field index independently depending on context. To this end,
the magic string `{index}` is replaced with the index or range as
required by context:

 - If the object is not an array, it is replaced with an empty string.
 - If the object is an array and the brief refers to the entire array
   or a slice thereof, it is replaced with `<low>..<high>`.
 - If the object is an array and the brief refers to a single index,
   it is simply replaced with just that index.

This key is optional unless required by context.

## `doc`

Extended documentation for the object. This is only used for
documentation output, and can therefore be any valid markdown. However,
avoid using `----` and `====` underlining for headers; instead use the
`#` prefix notation. `vhdmmio` will automatically prefix such headers
with additional hashes to get to the right header level. The brief
documentation is always added as a single paragraph before the extended
documentation.

Like the brief documentation, extended documentation may be printed
once for an array of fields or for each field index independently
depending on context. Therefore, `{index}` is replaced for `doc` in
exactly the same way.

This key is optional unless required by context.