"""Submodule for `Interrupt` configurables and friends."""

import re
from ...configurable import configurable, Configurable, choice, derive, checked, ParseError
from .registry import behavior, behavior_doc

behavior_doc('Fields for controlling `vhdmmio`-managed interrupts:')

@behavior(
    'interrupt', 'base class for interrupt field behaviors. Normally not used '
    'directly; it\'s easier to use one of its specializations:', 1)
@configurable(name='`interrupt` behavior')
class Interrupt(Configurable):
    """This is the base class for the behavior of interrupt fields, i.e. fields
    that operate on `vhdmmio`'s built-in interrupt system. They are associated
    with an interrupt defined in the `interrupts` key of the register file
    description. The arrayness of the interrupt must match the
    repetition/arrayness of the field descriptor, and the individual fields
    must be scalar."""
    #pylint: disable=E0211,E0213

    @checked
    def interrupt(self, value): #pylint: disable=R0201
        """The name of the interrupt or interrupt array that this field is
        associated with."""
        if not isinstance(value, str) or not re.fullmatch(r'[a-zA-Z][a-zA-Z0-9_]*', value):
            ParseError.invalid('', value, 'a string matching `[a-zA-Z][a-zA-Z0-9_]*`')
        return value

    @choice
    def mode():
        """The role that this field assumes for the associated interrupt."""
        yield 'raw', 'this field monitors the raw incoming interrupt request.'
        yield 'enable', 'this field monitors and/or controls the interrupt enable flag.'
        yield 'flag', 'this field monitors and/or controls the interrupt status flag.'
        yield 'unmask', 'this field monitors and/or controls the interrupt unmask flag.'
        yield 'masked', 'this field monitors the masked interrupt status flag.'

    @choice
    def bus_read():
        """Configures what happens when a bus read occurs."""
        yield 'disabled', 'read access is disabled.'
        yield 'enabled', 'read access is enabled.'
        yield 'clear', 'read access is enabled, and reading clears the associated flag.'

    @choice
    def bus_write():
        """Configures what happens when a bus read occurs."""
        yield 'disabled', 'write access is disabled.'
        yield 'enabled', 'write access is enabled.'
        yield 'clear', 'write access is enabled, and writing a one clears the associated flag.'
        yield 'set', 'write access is enabled, and writing a one sets the associated flag.'


@behavior(
    'interrupt-flag', 'interrupt pending flag, cleared by writing ones.', 1)
@derive(
    name='`interrupt-flag` behavior',
    mode='flag',
    bus_read=('enabled', 'disabled'),
    bus_write=('clear', 'disabled'))
class InterruptFlag(Interrupt):
    """This field behavior works much like a regular `flag` field, but operates
    on the interrupt pending flag of the associated interrupt instead of a
    field-specific register. The read value of the field is one if and only if
    the interrupt is pending, regardless of mask. Writing a one to the field
    clears the flag. If only one of these operations is needed, the other can
    be disabled.

    If the write mode of this field is enabled, the associated interrupt
    implicitly becomes strobe-sensitive.

    The arrayness of the interrupt must match the repetition/arrayness of the
    field descriptor. The individual fields must be scalar."""


@behavior(
    'volatile-interrupt-flag', 'interrupt pending flag, cleared by reading.', 1)
@derive(
    name='`volatile-interrupt-flag` behavior',
    mode='flag',
    bus_read='clear',
    bus_write='disabled')
class VolatileInterruptFlag(Interrupt):
    """This field behavior works much like a regular `volatile-flag` field, but
    operates on the interrupt pending flag of the associated interrupt instead
    of a field-specific register. The read value of the field is one if and
    only if the interrupt is pending, and the act of reading the field clears
    the interrupt pending status. Since the interrupt flag can be cleared, the
    associated interrupt implicitly becomes strobe-sensitive.

    The arrayness of the interrupt must match the repetition/arrayness of the
    field descriptor. The individual fields must be scalar."""


@behavior(
    'interrupt-pend', 'software-pend field.', 1)
@derive(
    name='`interrupt-pend` behavior',
    mode='flag',
    bus_read=['enabled'],
    bus_write='set')
class InterruptPend(Interrupt):
    """This field behavior allows software to set pend interrupts manually by
    writing a one, regardless of the enable flag or the incoming interrupt
    request. Since the interrupt flag can be set, the associated interrupt
    implicitly becomes strobe-sensitive, and needs a way to clear the flag as
    well. This can be done by reading this field when `bus-read` is set to
    `clear`, or through a (`volatile-`)`interrupt-flag` field.

    The arrayness of the interrupt must match the repetition/arrayness of the
    field descriptor. The individual fields must be scalar."""


@behavior(
    'interrupt-enable', 'interrupt enable control field.', 1)
@derive(
    name='`interrupt-enable` behavior',
    mode='enable',
    bus_read=('enabled', 'disabled'),
    bus_write=['enabled'])
class InterruptEnable(Interrupt):
    """This field behavior allows software to access the enable register
    for the associated interrupt. Incoming interrupt requests only affect the
    interrupt flag register when the enable register is set. If there is no
    way to enable an interrupt, it resets to the enabled state; otherwise it
    resets to disabled.

    The arrayness of the interrupt must match the repetition/arrayness of the
    field descriptor. The individual fields must be scalar."""


@behavior(
    'interrupt-unmask', 'interrupt unmask control field.', 1)
@derive(
    name='`interrupt-unmask` behavior',
    mode='unmask',
    bus_read=('enabled', 'disabled'),
    bus_write=['enabled'])
class InterruptUnmask(Interrupt):
    """This field behavior allows software to access the unmask register
    for the associated interrupt. A pending interrupt only asserts the outgoing
    interrupt flag signal when it is unmasked. If there is no way to unmask an
    interrupt, it resets to the unmasked state; otherwise it resets to masked.

    The arrayness of the interrupt must match the repetition/arrayness of the
    field descriptor. The individual fields must be scalar."""


@behavior(
    'interrupt-status', 'reflects the masked interrupt flag.', 1)
@derive(
    name='`interrupt-status` behavior',
    mode='masked',
    bus_read='enabled',
    bus_write='disabled')
class InterruptStatus(Interrupt):
    """This read-only field behavior reflects the state of the interrupt flag
    register masked by the interrupt mask register. It is one if and only if
    the interrupt is pending and unmasked.

    The arrayness of the interrupt must match the repetition/arrayness of the
    field descriptor. The individual fields must be scalar."""


@behavior(
    'interrupt-raw', 'reflects the raw interrupt request.', 1)
@derive(
    name='`interrupt-raw` behavior',
    mode='raw',
    bus_read='enabled',
    bus_write='disabled')
class InterruptRaw(Interrupt):
    """This read-only field behavior reflects the state of the raw incoming
    interrupt signal, regardless of whether the interrupt is enabled or whether
    the flag is set.

    The arrayness of the interrupt must match the repetition/arrayness of the
    field descriptor. The individual fields must be scalar."""
