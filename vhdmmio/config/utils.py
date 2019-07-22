"""Various utility objects and functions used within `vhdmmio.config`."""

class _UnsetType:
    """Used internally as an alternative to `None`, when `None` is already used
    for the `null` value in YAML/JSON."""

    def __eq__(self, other):
        return self is other

    def __str__(self):
        return 'Unset'

    __repr__ = __str__

Unset = _UnsetType() #pylint: disable=C0103


def friendly_yaml_value(value):
    """Convert Python's representation of a YAML value into a markdown-safe
    string representation of the YAML value for documentation and error
    messages."""
    if value is None:
        return '`null`'
    if value is True:
        return '`yes`'
    if value is False:
        return '`no`'
    return '`%s`' % value


def friendly_path(path):
    """Converts a path (list of strings for dict keys and ints for list
    indices) to a `.`/`[]` style name."""
    pretty = []
    for entry in path:
        if isinstance(entry, int) and pretty:
            pretty[-1] += '[%d]' % entry
        else:
            pretty.append(str(entry).replace('_', '-'))
    return '.'.join(pretty)


class ParseError(ValueError):
    """Error type used for reporting configuration parse errors."""
