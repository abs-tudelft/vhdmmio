"""Module for `Interrupt` objects."""

from .metadata import Metadata

class Interrupt:
    """Class representing the description of an interrupt or vector of
    interrupts.

    Every interrupt is associated with three internal registers:

     - enable: indicates that activation of the incoming IRQ signal pends the
       interrupt.
     - flag: indicates that the interrupt is pending.
     - unmasked: indicates that the outgoing IRQ signal is asserted when the
       interrupt is pending.

    These registers can be controlled through a number of fields in a number
    of different ways.

    If there is no way to clear the flag register, the incoming IRQ is
    level-sensitive. That is, when the external signal deasserts or the
    interrupt is disabled, the flag will also deassert. It is illegal to have
    a pend field in this case, as pending an interrupt is by definition a
    strobe-like operation.

    Interrupt flags always reset to cleared. Interrupts start disabled unless
    there is no way to disable them, and start masked unless there is no way
    to unmask them."""

    def __init__(self, regfile, **kwargs):
        """Constructs an interrupt from its YAML dictionary representation."""
        self._regfile = regfile
        self._can_enable = False
        self._can_clear = False
        self._can_pend = False
        self._can_unmask = False
        self._index = None

        # Parse metadata first, so we can print error messages properly.
        self._meta = Metadata.from_dict(1, kwargs.copy())
        try:

            # Parse vector width.
            self._width = kwargs.pop('width', None)
            if self._width is not None:
                self._width = int(self._width)

            # Parse metadata again, now with the correct vector width.
            self._meta = Metadata.from_dict(self._width, kwargs)

            # Check for unknown keys.
            for key in kwargs:
                raise ValueError('unexpected key in interrupt description: %s' % key)

        except (ValueError, TypeError) as exc:
            raise type(exc)('while parsing interrupt %s: %s' % (self._meta.name, exc))

    @classmethod
    def from_dict(cls, regfile, dictionary):
        """Constructs a interrupt descriptor object from a dictionary."""
        dictionary = dictionary.copy()
        for key in list(dictionary.keys()):
            if '-' in key:
                dictionary[key.replace('-', '_')] = dictionary.pop(key)
        return cls(regfile, **dictionary)

    def to_dict(self, dictionary=None):
        """Returns a dictionary representation of this object."""
        if dictionary is None:
            dictionary = {}

        # Write vector width.
        if self._width is not None:
            dictionary['width'] = self._width

        # Write metadata.
        self._meta.to_dict(dictionary)

        return dictionary

    @property
    def regfile(self):
        """Points to the parent register file."""
        return self._regfile

    @property
    def meta(self):
        """Metadata for this group of fields."""
        return self._meta

    @property
    def width(self):
        """Vector size of this interrupt, or `None` if the interrupt is
        scalar."""
        return self._width

    @property
    def index(self):
        """Index of this interrupt's LSB in the internal IRQ vector."""
        assert self._index is not None
        return self._index

    @index.setter
    def index(self, value):
        assert self._index is None
        self._index = value

    @property
    def low(self):
        """Index of this interrupt's LSB in the internal IRQ vector."""
        assert self._index is not None
        return self._index

    @property
    def high(self):
        """Index of this interrupt's MSB in the internal IRQ vector."""
        assert self._index is not None
        return self._index + self._width - 1

    @property
    def can_enable(self):
        """Indicates whether the interrupt can be enabled through a field. If
        there is no way to do this, the interrupt resets to the enabled
        state."""
        return self._can_enable

    @property
    def can_clear(self):
        """Indicates whether the interrupt can be cleared through a field. If
        there is no way to do this, the incoming interrupt signal is
        level-sensitive."""
        return self._can_clear

    @property
    def can_pend(self):
        """Indicates whether the interrupt can be pended through a field."""
        return self._can_pend

    @property
    def can_unmask(self):
        """Indicates whether the interrupt can be unmasked through a field. If
        there is no way to do this, the interrupt resets to the unmasked
        state."""
        return self._can_unmask

    def register_enable(self):
        """Registers that a field is present that can enable the interrupt."""
        self._can_enable = True

    def register_clear(self):
        """Registers that a field is present that can clear the interrupt."""
        self._can_clear = True

    def register_pend(self):
        """Registers that a field is present that can pend the interrupt."""
        self._can_pend = True

    def register_unmask(self):
        """Registers that a field is present that can unmask the interrupt."""
        self._can_unmask = True

    def check_consistency(self):
        """Consistency-checks this interrupt after all fields have been
        processed."""
        if self.can_pend and not self.can_clear:
            raise ValueError(
                'illegal pend field is present for level-sensitive interrupt %s '
                '(add a clear field to make it edge-sensitive)' % self.meta.name)

    def generate_vhdl(self, generator):
        """Generates the VHDL code for this interrupt by updating the given
        `vhdl.Generator` object."""
        # TODO
