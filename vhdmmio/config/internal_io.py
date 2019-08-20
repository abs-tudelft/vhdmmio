"""Submodule for `InterruptConfig` configurable."""

import re
from ..configurable import configurable, Configurable, choice, required_choice

@configurable(name='Internal signal I/O')
class InternalIOConfig(Configurable):
    """While vhdMMIO's field types and interrupts are already quite powerful on
    their own, their full power is only truly unlocked when they are used
    together. For instance, you may want to trigger an interrupt when a bus
    write occurs to an MMIO-to-stream field while the stream is blocked, to
    notify the software that it did something wrong. To support this and more
    without needing some external boilerplate logic (after all, the goal is to
    reduce such boilerplate logic as much as possible!), vhdMMIO supports
    specification of custom "internal" signals.

    An internal signal is automatically inferred when its name is referenced by
    an event source or sink. The name acts as a unique identifier, so
    specifying the same name twice will result in the components being tied
    together.

    Internal signals can be scalars (`std_logic`) or vectors
    (`std_logic_vector`), and can be level-based with a single driver, or
    strobe/event-based with one or more event sources (sometimes called
    `strobers`). The kind of internal signal that's associated with a name is
    usually implied by context. Of course, all endpoints that refer to an
    internal must agree to its kind, or vhdMMIO will send an error message your
    way.

    Sometimes, you may want to use or drive an data source or sink outside the
    register file. For instance, there may be a page register outside the
    register file that you want to use to select which page of registers is
    accessible. That's where this configuration structure comes in: it lets you
    associate a port with an internal signal, essentially making it an external
    signal."""
    #pylint: disable=E0211,E0213,E0202

    @required_choice
    def direction():
        """This key specifies what kind of I/O port should be made for the
        internal signal specified by `internal`."""
        yield ('input', 'an input port is generated for the internal. This '
               ' must be the internal signal\'s only driver.')
        yield ('strobe', 'an strobe input port is generated for the internal. '
               'The internal can be driven by other strobe sources as well; '
               'the result is wired-or.')
        yield ('output', 'an input port is generated for the internal.')

    @required_choice
    def internal():
        """This key specifies the name and shape of the internal signal."""
        yield (re.compile(r'[a-zA-Za-z][a-zA-Z0-9_]*'), 'a port is generated '
               'for a scalar internal with the given name.')
        yield (re.compile(r'[a-zA-Za-z][a-zA-Z0-9_]*:[0-9]+'), 'a port is '
               'generated for a vector internal with the given name and '
               'width.')

    @choice
    def port():
        """This key specifies the name of the port."""
        yield (None, 'the port is named after the internal signal.')
        yield (re.compile(r'[a-zA-Za-z][a-zA-Z0-9_]*'), 'the specified name '
               'is used for the port, regardless of the name of the internal '
               'signal.')

    @choice
    def group():
        """The I/O port for the internal signal can optionally be grouped
        along with other ports in a record. This key specifies the name of the
        group record."""
        yield None, 'port grouping is determined by the global default.'
        yield False, 'the port is not grouped in a record.'
        yield (re.compile(r'[a-zA-Z][a-zA-Z0-9_]*'),
               'the port is grouped in a record with the specified name.')
