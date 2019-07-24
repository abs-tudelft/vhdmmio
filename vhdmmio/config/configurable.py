"""Submodule containing the base class and annotations for `Configurable`
objects. Any object that contains loader must derive from `Configurable` and
have a `@configurable()` annotation. You can also make subclasses of these
objects. These are always subsets/specializations of the base class (through
the Liskov substitution principle). They must carry the `@derive()` annotation,
which allows defaults and value overrides to be specified."""

import textwrap
import inspect
from .loader import Loader

class Configurable:
    """Base class for objects that can be configured with/deserialized from
    and serialized to JSON/YAML-friendly dictionary form. When using this class
    as an ancestor, also use the `@configurable()` annotation."""

    def __init__(self, parent=None, dictionary=None, **kwargs):
        # Save the parent.
        self._parent = parent

        # If no dictionary was supplied, create an empty one.
        if dictionary is None:
            dictionary = {}

        # Update the dictionary with the kwargs. Together with the
        # previous, this allows a `Configurable` to be instantiated using
        # Pythonic keyword arguments in addition to the normal dictionary
        # deserialization method.
        for kwarg_key, value in kwargs:
            dict_key = kwarg_key.replace('_', '-')
            dictionary[dict_key] = value

        # Handle the loaders.
        for loader in self.loaders:
            setattr(
                self, '_' + loader.key,
                loader.deserialize(dictionary, self))

    @property
    def parent(self):
        """Returns the parent of this configurable. This is always another
        configurable, unless this is the root, in which case this is `None`."""
        return self._parent

    # The loaders of a configurable define which configuration keys are
    # supported and what their valid values are. This tuple is normally
    # overridden by the @configurable annotation, which looks for `Loader`
    # instances within the class definition. These are in turn constructed
    # from placeholder methods using method annotations. They are ordered;
    # that is, configuration keys are interpreted in the order in which
    # their loaders were defined in the class, so they can use the values
    # interpreted by previous loaders as contextual information. The
    # documentation output also maintains order.
    loaders = ()

    # Reserialization is essentially the inverse of the constructor, allowing
    # configuration files to be generated.
    def serialize(self, dictionary=None):
        """Serializes this object into its canonical dictionary
        representation."""
        if dictionary is None:
            dictionary = {}
        for loader in self.loaders:
            loader.serialize(dictionary, getattr(self, '_' + loader.key))
        return dictionary

    # A key aspect of `Configurable`s is that they can automatically generate
    # markdown documentation for their configuration dictionary. These
    # parameters are set by the `@configurable()` annotation.
    configuration_name = None
    configuration_doc = None

    @classmethod
    def configuration_markdown(cls):
        """Generates a markdown page for this class' configuration."""
        name = cls.configuration_name
        if name is None:
            name = '`%s`' % cls.__name__

        doc = cls.configuration_doc
        if doc is None:
            doc = cls.__doc__
        doc = inspect.cleandoc(doc)

        markdown = ['# %s%s' % (name[0].upper(), name[1:])]
        if doc:
            markdown.append(textwrap.dedent(doc))

        key_markdowns = []
        for loader in cls.loaders:
            for key, key_markdown in loader.markdown():
                if ' ' in key:
                    key_markdowns.append('## %s\n\n%s' % (key, key_markdown))
                else:
                    key_markdowns.append('## `%s`\n\n%s' % (key, key_markdown))
        if not key_markdowns:
            markdown.append('This structure does not support any configuration keys.')
        elif len(key_markdowns) == 1:
            markdown.append('This structure supports the following configuration key.')
        else:
            markdown.append('This structure supports the following configuration keys.')
        markdown.extend(key_markdowns)

        return '\n\n'.join(markdown)

    @classmethod
    def markdown_more(cls):
        """Yields `Configurable` classes that are referred to by the output of
        `configuration_markdown()`."""
        for loader in cls.loaders:
            #if loader.markdown_more() is None:
                #print(loader)
            for cfg in loader.markdown_more():
                if cfg is None:
                    print(loader)
                yield cfg


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

            # Define getter trivially.
            def getter(self, loader=loader):
                return getattr(self, '_' + loader.key)

            # If the loader supports mutation (that is, it has a validation
            # function). define a setter as well.
            if loader.mutable():
                def setter(self, value, loader=loader):
                    loader.validate(value)
                    setattr(self, '_' + loader.key, value)
            else:
                setter = None

            # Create the property (with protected setter).
            prop_name = loader.key.replace('-', '_')
            prop = property(getter, setter)
            setattr(cls, prop_name, prop)

            # Create the backing private variable.
            setattr(cls, '_' + prop_name, None)

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

        # Get the current loaders.
        loaders = {loader.key: loader for loader in cls.loaders}

        # Update the loaders.
        for key, value in mods.items():
            if key.startswith('_'):
                key = key[1:]
            key = key.replace('_', '-')
            if isinstance(value, list) and len(value) == 1:
                loaders[key] = loaders[key].with_default(value[0])
            elif isinstance(value, tuple) and len(value) == 1:
                loaders[key] = loaders[key].with_override(value[0])
            else:
                loaders[key] = loaders[key].with_override(value)

        # Gather any new loaders defined in the class. These loaders may also
        # override the loader for an existing key.
        for attr in dir(cls):
            attr = getattr(cls, attr)
            if isinstance(attr, Loader):
                loaders[attr.key] = attr

        # Set the new loader tuple.
        cls.loaders = tuple(sorted(loaders.values(), key=lambda loader: loader.order))

        # Update the documentation.
        cls.configuration_name = name
        cls.configuration_doc = doc

        return cls

    return decorator
