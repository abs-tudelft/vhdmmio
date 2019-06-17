"""Utility functions for parsing user-friendly dictionary-based options."""

def choice(dictionary, key, values):
    """Read/pop `key` from `dictionary`, checking that its value exists in
    the `values` list. If the key is not set, the first value in `values` is
    used as a default."""
    value = dictionary.pop(key, values[0])
    if value not in values:
        raise ValueError('%s must be one of %s' % (key, ', '.join(values)))
    return value

def switches(dictionary, key, values):
    """Read/pop switch keys from `dictionary`. Switch keys can be specified
    using an array of strings named `key`, where each string is an option
    from the `values` table, and/or using `<key>-<value>` keys along with
    the strings `enabled` or `disabled` or YAML booleans. The latter take
    precedence if both methods are used. The return value is a set of the
    values that were selected."""
    switch_values = dictionary.pop(key, [])
    if not isinstance(switch_values, list):
        raise ValueError('%s must be a list of strings' % key)
    for switch in switch_values:
        if switch not in values:
            raise ValueError('values for %s must be one of %s' % (key, ', '.join(values)))
    switch_values = set(switch_values)

    for value in values:
        switch = dictionary.pop(key, False)
        if switch == 'enabled':
            switch = True
        elif switch == 'disabled':
            switch = False
        if not isinstance(switch, bool):
            raise ValueError('%s-%s must be a boolean' % (key, value))
        if switch:
            switch_values.add(value)

    return switch_values

def override(dictionary, overrides):
    """Sets key-value pairs in `dictionary` based on `overrides`. Throws an
    error if the keys in `overrides` already exist."""
    for key, value in overrides.items():
        if key in dictionary and dictionary[key] != value:
            raise ValueError('%s is fixed to %s for this field type' % (key, value))
        dictionary[key] = value

def default(dictionary, defaults):
    """Sets key-value pairs in `dictionary` based on `defaults` if the
    respective keys did not exist yet."""
    for key, value in defaults.items():
        if key not in dictionary:
            dictionary[key] = value
