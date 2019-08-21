"""Submodule used for describing interrupts."""

from ..config.interface import InterfaceConfig
from .mixins import Shaped, Named, Configured, Unique
from .interface_options import InterfaceOptions

class Interrupt(Named, Shaped, Configured, Unique):
    """Represents an interrupt or a vector of interrupts."""

    def __init__(self, resources, regfile, cfg):
        super().__init__(
            cfg=cfg,
            metadata=cfg.metadata,
            doc_index='' if cfg.repeat is None else '*0..%d*' % (cfg.repeat - 1),
            shape=cfg.repeat)
        with self.context:
            resources.interrupt_namespace.add(self)
            self._regfile = regfile

            # Connect the fields that are associated with the interrupt and
            # record which operations can be performed using the bus.
            self._bus_can_enable = False
            self._bus_can_disable = False
            self._bus_can_pend = False
            self._bus_can_clear = False
            self._bus_can_unmask = False
            self._bus_can_mask = False
            self._offset, field_descriptors = resources.interrupts.register_interrupt(self)
            for field_descriptor in field_descriptors:
                field_descriptor.behavior.attach_interrupt(self)
                if field_descriptor.behavior.cfg.bus_write in ('enabled', 'set'):
                    if field_descriptor.behavior.cfg.mode == 'enable':
                        self._bus_can_enable = True
                    elif field_descriptor.behavior.cfg.mode == 'flag':
                        self._bus_can_pend = True
                    else:
                        assert field_descriptor.behavior.cfg.mode == 'unmask'
                        self._bus_can_unmask = True
                if (field_descriptor.behavior.cfg.bus_write in ('enabled', 'clear')
                        or field_descriptor.behavior.cfg.bus_read == 'clear'):
                    if field_descriptor.behavior.cfg.mode == 'enable':
                        self._bus_can_disable = True
                    elif field_descriptor.behavior.cfg.mode == 'flag':
                        self._bus_can_clear = True
                    else:
                        assert field_descriptor.behavior.cfg.mode == 'unmask'
                        self._bus_can_mask = True

            # Check configuration for as far as we can. There are some
            # additional checks in `InterruptManager.finish()`, which we can
            # only do after we know what kind of internal signal we're attached
            # to (if any).
            if self._bus_can_pend and not self._bus_can_clear:
                raise ValueError(
                    'cannot trigger level-sensitive interrupt with software '
                    'pend field; add a way to clear the interrupt flag using '
                    'the bus to fix this')
            if self.level_sensitive and self.active not in ('high', 'low'):
                raise ValueError(
                    'interrupt cannot be edge-sensitive if there is no field '
                    'that can clear the interrupt flag afterwards')

            # Connect the interrupt source.
            if cfg.internal is None:
                self._is_internal = False
                self._signal = self.name
            else:
                self._is_internal = True
                self._signal = resources.internals.use(self, cfg.internal, self.shape)

            # Determine the interface options.
            self._interface_options = InterfaceOptions(
                regfile.cfg.interface,
                InterfaceConfig(group=cfg.group, flatten=True))

    @property
    def regfile(self):
        """The register file that this interrupt belongs to."""
        return self._regfile

    def is_external(self):
        """Returns whether this is an interrupt sourced by an external
        signal."""
        return not self._is_internal

    @property
    def external_signal(self):
        """The name of the external signal related to this interrupt, or
        `None` if there is no such signal."""
        if not self.is_external():
            return None
        return self._signal

    def is_internal(self):
        """Returns whether this is an interrupt sourced by an internal
        signal."""
        return self._is_internal

    @property
    def internal(self):
        """The internal signal object related to this interrupt, or `None` if
        there is no such signal."""
        if not self.is_internal():
            return None
        return self._signal

    @property
    def bus_can_enable(self):
        """Whether there is a way for this interrupt to be enabled through the
        bus."""
        return self._bus_can_enable

    @property
    def bus_can_disable(self):
        """Whether there is a way for this interrupt to be disabled through the
        bus."""
        return self._bus_can_disable

    @property
    def enabled_after_reset(self):
        """Whether the interrupt initializes to being enabled."""
        return not self._bus_can_enable

    @property
    def bus_can_pend(self):
        """Whether there is a way for this interrupt to be pended using the
        bus."""
        return self._bus_can_pend

    @property
    def bus_can_clear(self):
        """Whether there is a way for this interrupt to be cleared using the
        bus."""
        return self._bus_can_clear

    @property
    def level_sensitive(self):
        """Whether this interrupt is level-sensitive. If true, the interrupt
        source cannot be a strobe signal, the interrupt cannot be
        edge-sensitive, and the interrupt cannot be software-pended."""
        return not self._bus_can_clear

    @property
    def bus_can_unmask(self):
        """Whether there is a way for this interrupt to be unmasked through the
        bus."""
        return self._bus_can_unmask

    @property
    def bus_can_mask(self):
        """Whether there is a way for this interrupt to be masked through the
        bus."""
        return self._bus_can_mask

    @property
    def unmasked_after_reset(self):
        """Whether the interrupt initializes to being unmasked."""
        return not self._bus_can_unmask

    @property
    def offset(self):
        """The index offset for this interrupt or interrupt vector, such that
        each scalar interrupt is assigned a number starting at zero."""
        return self._offset

    @property
    def active(self):
        """The triggering condition for the interrupt, one of:

         - `'high'`: the interrupt is level/strobe-sensitive, active-high;
         - `'low'`: the interrupt is level/strobe-sensitive, active-low;
         - `'rising'`: the interrupt is rising-edge sensitive;
         - `'falling'`: the interrupt is falling-edge sensitive;
         - `'edge'`: the interrupt is sensitive to any edge.
        """
        return self.cfg.active

    @property
    def interface_options(self):
        """VHDL interface configuration."""
        return self._interface_options


class InterruptManager:
    """Resource object for mapping interrupt names to fields as the fields get
    constructed. When the interrupts are subsequently constructed, they pop the
    fields belonging from them from the manager and complete the connection. If
    any interrupt names are left over after this process, an error is
    generated."""

    def __init__(self):
        super().__init__()
        self._interrupt_to_field_descriptors = {}
        self._interrupts = []
        self._concat_width = 0

    def register_field_descriptor(self, field_descriptor):
        """Registers an interrupt field."""
        interrupt = field_descriptor.cfg.behavior.interrupt
        fields = self._interrupt_to_field_descriptors.get(interrupt, None)
        if fields is None:
            fields = []
            self._interrupt_to_field_descriptors[interrupt] = fields
        fields.append(field_descriptor)

    def register_interrupt(self, interrupt):
        """Registers an interrupt, and pops and returns the field descriptor
        list for that interrupt."""
        offset = self._concat_width
        self._interrupts.append(interrupt)
        self._concat_width += interrupt.width
        return offset, self._interrupt_to_field_descriptors.pop(interrupt.name, [])

    @property
    def concat_width(self):
        """The width of the vector that results when all interrupts are
        concatenated together."""
        return self._concat_width

    def __iter__(self):
        """Iterates over the registered interrupts."""
        return iter(self._interrupts)

    def verify(self):
        """Checks that all fields and interrupts are connected properly."""

        # Check that all interrupt fields have been connected to interrupts.
        for fields in self._interrupt_to_field_descriptors.values():
            for field in fields:
                with field.context:
                    raise ValueError('interrupt does not exist')

        # Perform some final checks on the interrupt configuration that depend
        # on the type of internal signal associated with the interrupt.
        for interrupt in self._interrupts:
            if interrupt.is_internal() and interrupt.internal.is_strobe():
                with interrupt.context:
                    if interrupt.level_sensitive:
                        raise ValueError(
                            'cannot trigger level-sensitive interrupt with '
                            'internal strobe signal; add a way to clear the '
                            'interrupt flag using the bus to fix this')
                    if interrupt.active != 'high':
                        raise ValueError(
                            'interrupts triggered by internal strobe signals '
                            'must be active-high')


class InterruptInfo:
    """Exposes information gathered by `InterruptManager` in an immutable
    way."""

    def __init__(self, manager):
        super().__init__()
        self._concat_width = manager.concat_width
        strobe_mask = []
        umsk_reset = []
        enab_reset = []
        for interrupt in manager:
            if interrupt.bus_can_clear:
                strobe_mask.append('1' * interrupt.width)
            else:
                strobe_mask.append('0' * interrupt.width)
            if interrupt.unmasked_after_reset:
                umsk_reset.append('1' * interrupt.width)
            else:
                umsk_reset.append('0' * interrupt.width)
            if interrupt.enabled_after_reset:
                enab_reset.append('1' * interrupt.width)
            else:
                enab_reset.append('0' * interrupt.width)
        self._strobe_mask = ''.join(reversed(strobe_mask))
        self._umsk_reset = ''.join(reversed(umsk_reset))
        self._enab_reset = ''.join(reversed(enab_reset))
        assert len(self.strobe_mask) == self._concat_width
        assert len(self.umsk_reset) == self._concat_width
        assert len(self.enab_reset) == self._concat_width

    @property
    def concat_width(self):
        """The width of the vector that results when all interrupts are
        concatenated together."""
        return self._concat_width

    @property
    def strobe_mask(self):
        """The MSB-first bit vector containing the mask applied to `flag` every
        cycle, to clear level-sensitive interrupts."""
        return self._strobe_mask

    @property
    def umsk_reset(self):
        """The MSB-first bit vector containing the reset value for the `umsk`
        register for each interrupt."""
        return self._umsk_reset

    @property
    def enab_reset(self):
        """The MSB-first bit vector containing the reset value for the `enab`
        register for each interrupt."""
        return self._enab_reset
