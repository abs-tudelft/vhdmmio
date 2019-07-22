"""Submodule containing the base class and annotations for `Configurable`
objects. Any object that contains loader must derive from `Configurable` and
have a `@configurable()` annotation. You can also make subclasses of these
objects. These are always subsets/specializations of the base class (through
the Liskov substitution principle). They must carry the `@derive()` annotation,
which allows defaults and value overrides to be specified."""

import textwrap
import inspect
from .loader import Loader
from .utils import ParseError, friendly_path

class Configurable:
    """Base class for objects that can be configured with/deserialized from
    and serialized to JSON/YAML-friendly dictionary form."""

    loaders = ()
    configuration_name = None
    configuration_doc = None

    @classmethod
    def from_dict(cls, dictionary, *args):
        """Constructs this class from its dictionary serialization."""
        dictionary = dictionary.copy()
        for key in list(dictionary.keys()):
            if '-' in key:
                dictionary[key.replace('-', '_')] = dictionary.pop(key)
        return cls(*args, **dictionary)

    def to_dict(self, dictionary=None):
        """Serializes this object into its canonical dictionary
        representation."""
        if dictionary is None:
            dictionary = {}
        for loader in self.loaders:
            loader.serialize(dictionary, getattr(self, '_' + loader.key))
        return dictionary

    @classmethod
    def configuration_markdown(cls):
        """Generates a markdown page for this class' configuration."""
        name = cls.configuration_name
        if name is None:
            name = '`%s`' % cls.__name__

        doc = cls.configuration_doc
        if doc is None:
            doc = cls.__doc__

        markdown = ['# %s%s' % (name[0].upper(), name[1:])]
        if doc:
            markdown.append(textwrap.dedent(doc))
        markdown.append(
            'The following configuration keys are supported by %s objects.' % name)
        for loader in cls.loaders:
            for key, key_markdown in loader.markdown():
                if ' ' in key:
                    markdown.append('## %s' % key)
                else:
                    markdown.append('## `%s`' % key)
                markdown.append(key_markdown)
        return '\n\n'.join(markdown)


def configurable(*loaders, name=None, doc=None):
    """Decorator that makes a class that can be constructed from a
    JSON/YAML-friendly dictionary representation, and can also be turned back
    into one.

    The arguments to the decorator must be `Loader`s that represent the
    configurable properties that will be added to the class and how they are
    loaded.

    Underscores and dashes in the dictionary keys are equivalent; any dashes in
    keys are replaced with underscores in the generated `from_dict()` function.
    Dashes are preferred (they are more idiomatic in YAML); underscores are
    useful when constructing classes from within Python using keyword
    arguments. Internally, only underscores are used."""

    def decorator(cls, loaders=loaders):

        # Gather loaders defined in the class.
        loaders = list(loaders)
        for attr in dir(cls):
            attr = getattr(cls, attr)
            if isinstance(attr, Loader):
                loaders.append(attr)
        loaders = tuple(sorted(loaders, key=lambda loader: loader.order))

        # Add loaders property.
        cls.loaders = loaders

        # Add a value property for each loader's key.
        for loader in loaders:
            def getter(self, loader=loader):
                return getattr(self, '_' + loader.key)
            prop = property(getter)
            setattr(cls, loader.key, prop)
            setattr(cls, '_' + loader.key, None)

        # Patch the __init__ function to take serialized data from **kwargs.
        user_initializer = cls.__init__

        accept_keyword_args = set()
        for key, param in inspect.signature(user_initializer).parameters.items():
            if param.kind in (param.POSITIONAL_OR_KEYWORD, param.KEYWORD_ONLY):
                if param.default is not param.empty:
                    accept_keyword_args.add(key)
            if param.kind == param.VAR_KEYWORD:
                accept_keyword_args = True

        def initializer(self, *args, configurable_path=(), **kwargs):
            for loader in self.loaders:
                setattr(
                    self, '_' + loader.key,
                    loader.deserialize(kwargs, self, configurable_path))

            if accept_keyword_args is not True:
                for key in kwargs:
                    if key not in accept_keyword_args:
                        if configurable_path == ():
                            raise ParseError(
                                'unknown key for configuration file: `%s`'
                                % key.replace('_', '-'))
                        raise ParseError(
                            'unknown key for %s: `%s`' % (
                                friendly_path(configurable_path),
                                key.replace('_', '-')))
            user_initializer(self, *args, **kwargs)

        cls.__init__ = initializer

        # Add the documentation, if specified through the decorator.
        cls.configuration_name = name
        cls.configuration_doc = doc

        return cls

    return decorator


def derive(name=None, doc=None, **mods):
    """Decorator for making derived `configurable`s. Allows `ScalarLoader` keys
    to be updated with different default values, or overriding their value
    altogether. The new defaults and overrides are specified using the keyword
    arguments, where the key is the name of the key to modify, and the value is
    either a list with a single item containing the new default value, or an
    override value (so defaults look like `[default]` and overrides are just
    `override`; this seems like a good idea at the time). Overriding with a
    single-item list is possible by escaping the override by putting it in a
    single-item tuple. Escaping the `name` and `doc` keyword arguments is
    possible by prefixing an underscore to the modification key."""

    def decorator(cls, mods=mods): #pylint: disable=W0102
        loaders = {loader.key: loader for loader in cls.loaders}

        # Update the loaders.
        for key, value in mods.items():
            if key.startswith('_'):
                key = key[1:]
            if isinstance(value, list) and len(value) == 1:
                loaders[key] = loaders[key].set_default(value[0])
            elif isinstance(value, tuple) and len(value) == 1:
                loaders[key] = loaders[key].override(value[0])
            else:
                loaders[key] = loaders[key].override(value)
        cls.loaders = tuple(loaders.values())

        # Update the documentation.
        cls.configuration_name = name
        cls.configuration_doc = doc

        return cls

    return decorator
