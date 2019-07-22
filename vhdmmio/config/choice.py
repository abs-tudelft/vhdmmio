"""Submodule for `Choice` loaders. These loaders handle scalar values
(strings, integers, or booleans) that can take two or more different values
and have a default value. All error checking and parsing is handled by the
`Choice` `Loader`, and documentation for the possible values is also
generated to make sure it stays in sync with the source code."""

import textwrap
from .loader import ScalarLoader
from .utils import Unset, ParseError, friendly_yaml_value

class Choice(ScalarLoader):
    """Loader for regular keys, where a user can choose between a number of
    options, of which the first one is the default. Choices are specified as
    `(spec, markdown)` tuples, where `spec` is an integer, boolean, or string
    that must match exactly, `None` for `null`, a compiled regex object that
    must match, a two-tuple specifying a valid integer range, a type (so only
    the type has to match), or a function that does the conversion, and
    `markdown` is the documentation for what that value does. The first choice
    must be an exact value or `None`. A conversion function may only be used
    for the last argument. For conversion functions, the documentation is
    generated from the function's docstring. Conversion function must return
    something whose `str()` representation performs the inverse of the
    conversion function."""

    def __init__(self, key, markdown, *choices, default=Unset):
        if default is not Unset:
            default = choices[0][0]
            if default is bool:
                default = False
        if not isinstance(default, (int, str, bool)) and default is not None:
            raise ValueError('invalid default value')
        super().__init__(key, markdown, default, Unset)
        self._choices = choices

        # Run get_friendly_choices() to do error checking, but don't store the
        # value: we might get copied and have our default mutated, so we need
        # to recalculate on-the-fly as needed.
        self._get_friendly_choices()

    def _parse_value(self, value):
        """Tries to parse the given value against the choice list, returning
        a two-tuple of the choice list index and the (possibly converted) value
        if found, or `(None, None)` if not found."""
        for index, (choice_desc, _) in enumerate(self._choices):
            if isinstance(choice_desc, (int, str, bool)):
                if value == choice_desc:
                    return index, value

            elif choice_desc is None:
                if value is None:
                    return index, value

            elif hasattr(choice_desc, 'fullmatch'):
                if isinstance(value, str) and choice_desc.fullmatch(value):
                    return index, value

            elif isinstance(choice_desc, tuple):
                if isinstance(value, int):
                    if choice_desc[0] is None or value >= choice_desc[0]:
                        if choice_desc[1] is None or value < choice_desc[1]:
                            return index, value

            elif isinstance(choice_desc, type):
                if isinstance(value, choice_desc):
                    return index, value

            else:
                return index, choice_desc(value)

        return None, None

    def _get_friendly_choices(self):
        """Formats each entry in the `self._choices` list as a friendly string
        for documentation and error messages. If there is an override, a list
        with just the override item is returned."""
        if self.is_overridden():
            return ['%r (default)' % (self.override_value,)]

        friendly_choices = []
        ints_found = False
        strings_found = False
        bools_found = False
        function_found = False

        for choice_desc, _ in self._choices:
            if function_found:
                raise ValueError('interpreter function must be the last choice')

            if isinstance(choice_desc, int):
                friendly_choices.append('`%d`' % choice_desc)
                ints_found = True

            elif isinstance(choice_desc, str):
                friendly_choices.append('`%s`' % choice_desc)
                strings_found = True

            elif isinstance(choice_desc, bool):
                if choice_desc:
                    friendly_choices.append('`true`')
                else:
                    friendly_choices.append('`false`')
                bools_found = True

            elif choice_desc is None:
                friendly_choices.append('`null`')

            elif hasattr(choice_desc, 'fullmatch'):
                friendly_choices.append('a string matching `%s`' % choice_desc.pattern)
                strings_found = True

            elif isinstance(choice_desc, tuple):
                if choice_desc[0] is None:
                    if choice_desc[1] is None:
                        if ints_found:
                            friendly_choices.append('a different integer')
                        else:
                            friendly_choices.append('an integer')
                    else:
                        friendly_choices.append('an integer below %d' % choice_desc[1])
                elif choice_desc[1] is None:
                    friendly_choices.append('an integer above or equal to %d' % choice_desc[0])
                else:
                    friendly_choices.append('an integer between %d and %d' % choice_desc)
                ints_found = True

            elif choice_desc is int:
                if ints_found:
                    friendly_choices.append('a different integer')
                else:
                    friendly_choices.append('an integer')
                    ints_found = True

            elif choice_desc is str:
                if strings_found:
                    friendly_choices.append('a different string')
                else:
                    friendly_choices.append('a string')
                    strings_found = True

            elif choice_desc is bool:
                if bools_found:
                    friendly_choices.append('a different boolean')
                else:
                    friendly_choices.append('a boolean')
                    bools_found = True

            elif callable(choice_desc):
                friendly_choices.append('interpretable by %s' % choice_desc.__name__)
                function_found = True

            else:
                raise ValueError('unknown spec type')

        if self.has_default():
            default_index, _ = self._parse_value(self.default)
            assert default_index is not None
            if self._choices[default_index][0] == self.default:
                add = ' (default)'
            else:
                add = ' (default %s)' % friendly_yaml_value(self.default)
            friendly_choices[default_index] += add

        return friendly_choices

    def deserialize(self, dictionary, _, path=()):
        """`Choice` deserializer. See `Loader.deserialize()` for more info."""
        index, value = self._parse_value(self.get_value(dictionary, path))
        if index is not None:
            return value

        friendly_choices = self._get_friendly_choices()

        if len(friendly_choices) == 1:
            friendly_choices = friendly_choices[0]
        elif len(friendly_choices) == 2:
            friendly_choices = '%s or %s' % tuple(friendly_choices)
        else:
            friendly_choices = '%s, or %s' % (
                ', '.join(friendly_choices[:-1]), friendly_choices[-1])

        raise ParseError('%s must be %s, but was %s' % (
            self.friendly_path(path), friendly_choices, friendly_yaml_value(value)))

    def scalar_serialize(self, value):
        """Converts the internal value into its serialized representation."""
        if not isinstance(value, (int, str, bool)) and value is not None:
            value = str(value)
        return value

    def scalar_markdown(self):
        """Extra markdown paragraphs representing the choices."""
        if len(self._choices) == 1:
            choice_markdown = textwrap.dedent(self._choices[0][1]).replace('\n', '\n   ')
            if choice_markdown:
                choice_markdown = ': ' + choice_markdown
            else:
                choice_markdown = '.'
            yield 'The value must be %s%s' % (
                self._get_friendly_choices()[0],
                choice_markdown)
        else:
            yield 'The following values are supported:'
            for (_, choice_markdown), choice_description in zip(
                    self._choices, self._get_friendly_choices()):
                choice_markdown = textwrap.dedent(choice_markdown).replace('\n', '\n   ')
                if choice_markdown:
                    choice_markdown = ': ' + choice_markdown
                else:
                    choice_markdown = '.'
                yield ' - %s%s' % (choice_description, choice_markdown)


def choice(method):
    """Method decorator for constructing `Choice` loaders inside a
    `configurable`-annotated class. The annotated method must yield or return
    `(choice, doc)` two-tuples, where `choice` is one of the many choice
    descriptors (see `Choice`) and `doc` is the documentation for that choice.
    The method should not take any arguments, not even `self` (so a pylint
    disable marker is unfortunately required). The name of the key is set to
    the name of the method, and the markdown documentation for the key is set
    to the method's docstring."""
    return Choice(method.__name__, method.__doc__, *method())


def flag(method):
    """Convenience method for making flag `Choice`s, i.e. booleans that default
    to `False`. The return value of the annotated method (cast to bool) is used
    as the default value. The method should not take any arguments; not even
    `self`."""
    return Choice(method.__name__, method.__doc__, (bool, ''), bool(method()))