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

    class _AutoGenDefault: #pylint: disable=R0903
        pass

    def __init__(self, key, doc, *choices, default=_AutoGenDefault):
        if default is Choice._AutoGenDefault:
            default = choices[0][0]
        if not isinstance(default, (int, str, bool)):
            if default is not None and default is not Unset:
                raise ValueError('invalid default value')
        super().__init__(key, doc, default, Unset)
        self._choices = choices

        # Run get_friendly_choices() to do error checking, but don't store the
        # value: we might get copied and have our default mutated, so we need
        # to recalculate on-the-fly as needed.
        self._get_friendly_choices()

    def _parse_value(self, value):
        """Tries to match the given value against the choice list, returning
        the choice list index if found, or `None` if not found."""
        for index, (choice_desc, _) in enumerate(self._choices):
            if isinstance(choice_desc, (int, str, bool)):
                if value == choice_desc:
                    return index

            elif choice_desc is None:
                if value is None:
                    return index

            elif hasattr(choice_desc, 'fullmatch'):
                if isinstance(value, str) and choice_desc.fullmatch(value):
                    return index

            elif isinstance(choice_desc, tuple):
                if hasattr(choice_desc[0], 'fullmatch'):
                    if isinstance(value, str) and choice_desc[0].fullmatch(value):
                        return index

                elif isinstance(value, int):
                    if choice_desc[0] is None or value >= choice_desc[0]:
                        if choice_desc[1] is None or value < choice_desc[1]:
                            return index

            elif isinstance(choice_desc, type):
                if isinstance(value, choice_desc):
                    return index

            else:
                return index, choice_desc(value)

        return None

    def _get_friendly_choices(self):
        """Formats each entry in the `self._choices` list as a friendly string
        for documentation and error messages. If there is an override, a list
        with just the override item is returned."""
        if self.has_override():
            return ['%s (default)' % (friendly_yaml_value(self.override))]

        friendly_choices = []
        ints_found = False
        strings_found = False
        bools_found = False
        function_found = False

        for choice_desc, _ in self._choices:
            if function_found:
                raise ValueError('interpreter function must be the last choice')

            if isinstance(choice_desc, bool):
                friendly_choices.append(friendly_yaml_value(choice_desc))
                bools_found = True

            elif isinstance(choice_desc, int):
                friendly_choices.append(friendly_yaml_value(choice_desc))
                ints_found = True

            elif isinstance(choice_desc, str):
                friendly_choices.append(friendly_yaml_value(choice_desc))
                strings_found = True

            elif choice_desc is None:
                friendly_choices.append(friendly_yaml_value(choice_desc))

            elif hasattr(choice_desc, 'fullmatch'):
                friendly_choices.append('a string matching `%s`' % choice_desc.pattern)
                strings_found = True

            elif isinstance(choice_desc, tuple) and hasattr(choice_desc[0], 'fullmatch'):
                friendly_choices.append(choice_desc[1])
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
            default_index = self._parse_value(self.default)
            assert default_index is not None
            if self._choices[default_index][0] == self.default:
                add = ' (default)'
            else:
                add = ' (default %s)' % friendly_yaml_value(self.default)
            friendly_choices[default_index] += add

        return friendly_choices

    def deserialize(self, dictionary, _):
        """`Choice` deserializer. See `Loader.deserialize()` for more info."""
        value = self.get_value(dictionary)
        self.validate(value)
        return value

    def scalar_serialize(self, value):
        """Converts the internal value into its serialized representation."""
        if not isinstance(value, (int, str, bool)) and value is not None:
            value = str(value)
        return value

    def mutable(self):
        """Returns whether the value managed by this loader can be mutated. If
        this is overridden to return `True`, the loader must implement
        `validate()`."""
        return True

    def validate(self, value):
        """Checks that the given value is valid for this loader, raising an
        appropriate ParseError if not. This function only needs to work if
        `mutable()` returns `True`."""
        if self._parse_value(value) is None:
            ParseError.invalid(self.key, value, *self._get_friendly_choices())

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

    def with_mods(self, *choices_to_keep):
        """Returns a modified `Choice`, where only the choices listed in
        `choices_to_keep` are present, in that order. The first choice listed
        becomes the new default value. Choices can be specified either as just
        a descriptor or as a two-tuple of a descriptor and a new documentation
        string."""
        current_choices = {desc: doc for desc, doc in self._choices}
        new_choices = []
        for choice_tuple in choices_to_keep:
            desc, doc = choice_tuple if isinstance(choice_tuple, tuple) else (choice_tuple, None)
            current_doc = current_choices.pop(desc)
            if doc is None:
                doc = current_doc
            new_choices.append((desc, doc))
        new_choice = Choice(self.key, self.doc, *new_choices)
        new_choice.order = self.order
        return new_choice


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


def required_choice(method):
    """Same as `choice`, but instead of generating the default value from the
    first choice, there is no default value, making the key required.."""
    return Choice(method.__name__, method.__doc__, *method(), default=Unset)


def choice_default(default):
    """Same as `choice`, but called with the desired default value as an
    argument to the annotation."""
    def annotate(method, default=default):
        """Annotation function."""
        return Choice(method.__name__, method.__doc__, *method(), default=default)
    return annotate


def flag(method):
    """Convenience method for making flag `Choice`s, i.e. booleans that default
    to `False`. The return value of the annotated method (cast to bool) is used
    as the default value. The method should not take any arguments; not even
    `self`."""
    return Choice(method.__name__, method.__doc__, (bool, ''), default=bool(method()))
