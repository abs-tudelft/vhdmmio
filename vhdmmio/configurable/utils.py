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
    if value is Unset:
        return 'left unspecified'
    if isinstance(value, list):
        return 'a list'
    if isinstance(value, dict):
        return 'a dictionary'
    return '`%s`' % value


class ParseError(ValueError):
    """Error type used for reporting configuration parse errors. The exception
    is intended to be updated with contextual information as it propagates up
    to the configuration file hierarchy through `context()` and `path()`. The
    latter updates the configuration key path, which can be used in the message
    using `{path}`."""

    def __init__(self, message, path=''):
        super().__init__()
        self._message = message
        self._path = '[%d]' % path if isinstance(path, int) else path

    def context(self, prefix):
        """Adds contextual information to the front of the message."""
        self._message = '%s: %s' % (prefix, self._message)

    def path(self, prefix):
        """Adds a configuration key path entry to the front of the `ParseError`
        path."""
        if isinstance(prefix, int):
            prefix = '[%d]' % prefix
        if self._path and not self._path[0] == '[':
            prefix += '.'
        self._path = prefix + self._path

    def __str__(self):
        path = self._path
        if not path:
            path = '<root>'
        return self._message.format(path=path)

    def __repr__(self):
        return 'ParseError(%r)' % str(self)

    @classmethod
    def required(cls, key):
        """Raises an appropriate `ParseError` for a missing required key."""
        raise cls('{path} requires key %s to be defined' % key)

    @classmethod
    def invalid(cls, key, value, *expected):
        """Raises an appropriate `ParseError` for an overridden key with the
        wrong value."""
        if len(expected) <= 2:
            phrase = ' or '.join(expected)
        else:
            phrase = '%s, or %s' % (', '.join(expected[:-1]), expected[-1])
        raise cls('{path} must be %s, but was %s' % (phrase, friendly_yaml_value(value)), key)

    @classmethod
    def unknown(cls, *keys):
        """Raises an appropriate `ParseError` for the given unknown keys in a
        configuration dictionary."""
        assert keys
        if len(keys) <= 2:
            phrase = '`%s`' % '` and `'.join(keys)
        else:
            phrase = '`%s`, and `%s`' % ('`, `'.join(keys[:-1]), keys[-1])
        raise cls('unknown key%s %s in {path}' % ('s' if len(keys) > 1 else '', phrase))

    @classmethod
    def wrap(cls, key=''):
        """Returns a context manager that wraps common exceptions in
        `ParseError`s. It also adds configuration key path context to any
        `ParseError`s that get raised as a form of traceback."""
        class ParseErrorContext:
            """Context manager for `ParseError.wrap()`."""
            def __enter__(self):
                return self
            def __exit__(self, typ, val, trace):
                if val is not None:
                    if issubclass(typ, ParseError):
                        if key is not None:
                            val.path(key)
                        return
                    raise cls('while parsing {path}: %s' % val, path=key)
        return ParseErrorContext()
