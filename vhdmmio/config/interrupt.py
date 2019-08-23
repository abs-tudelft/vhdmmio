"""Submodule for `InterruptConfig` configurable."""

import re
from ..configurable import configurable, Configurable, choice, embedded
from .metadata import MetadataConfig

@configurable(name='Interrupt descriptors')
class InterruptConfig(Configurable):
    r"""In addition to MMIO, `vhdmmio` can handle interrupt routing for you.
    Each AXI4-lite bus is equiped with an additional signal in the
    slave-to-master direction that serves as an interrupt request flag. This
    flag is connected to a (masked) wired-or network of any incoming interrupts
    you define.

    ## Behavior

    The interrupts can be monitored and controlled through fields with the
    (`interrupt`)[interrupt.md] behavior.

    There are up to three internal registers for each interrupt, named `enab`
    (short for enable), `flag`, and `umsk` (short for unmask). `enab` controls
    whether incoming interrupts are passed on to the flag register. The flag
    register stores whether the interrupt is pending regardless of whether it
    is enabled; if an interrupt comes in while the interrupt is enabled, and
    the interrupt is then disabled, the flag remains asserted until it is
    explicitly cleared (usually by an interrupt handler). `umsk` (unmask) has a
    similar function, but is placed after the flag register. Thus, masking an
    interrupt immediately stops it from being requested, but once the interrupt
    is unmasked again, it will be requested again. This logic is shown
    schematically below.

    ```
                .--[raw>
                |         ____                 flag
    IRQ --------o--------|    \     _____     .----.   .-[flag>
                         |     )----\    \    |>   |   |         ____
                      .--|____/      )    )---|S  Q|---o--------|    \     to
               enab   |      [pend>-/____/  .-|R   |  umsk      |     )--> wired
              .----.  |      [clear>--------' '----' .----.  .--|____/     OR
              |>   |  |                              |>   |  |
    [enable>--|S  Q|--o--[enabled>          [unmask>-|S  Q|--o--[unmasked>
    [disable>-|R   |                        [mask>---|R   |
              '----'                                 '----'
    ```

    Each of the three registers are accessible in read, write, set, and clear
    modes through fields with (`interrupt`)[interrupt.md] behavior. The raw
    incoming interrupt signal and the masked output signal of an interrupt can
    also be monitored directly.

    Interrupts can be made level-sensitive by not specifying a way to clear the
    interrupt. In this case, the logic is automatically simplified to the
    following.

    ```
                .--[raw>
                |         ____                 .-[flag>
    IRQ --------o--------|    \                |         ____
                         |     )---------------o--------|    \     to
                      .--|____/                         |     )--> wired
               enab   |                       umsk   .--|____/     OR
              .----.  |                      .----.  |
              |>   |  |                      |>   |  |
    [enable>--|S  Q|--o--[enabled>  [unmask>-|S  Q|--o--[unmasked>
    [disable>-|R   |                [mask>---|R   |
              '----'                         '----'
    ```

    Furthermore, if there is no way to enable/unmask an interrupt, the
    respective AND gate and the register is effectively optimized away. If
    there *is* a way, the reset state is disabled/masked.

    ## Interrupt sources

    A `vhdmmio` interrupt can currently be requested through an internal or
    synchronous external signal, or by software using the
    [`interrupt-pend`](interruptpend.md) field behavior. An external
    synchronizer is needed to accept asynchronous interrupts. These are often
    vendor-specific, therefore they are not included in vhdmmio."""
    #pylint: disable=E0211,E0213,E0202

    @choice
    def repeat():
        """This value specifies whether this interrupt descriptor describes a
        single interrupt or an array of interrupts."""
        yield None, 'the descriptor describes a single interrupt.'
        yield (1, None), ('the descriptor describes an array of interrupts of '
                          'the given size.')

    @embedded
    def metadata():
        """This configuration structure is used to name and document the
        interrupt."""
        return MetadataConfig

    @choice
    def internal():
        """This key specifies whether the interrupt is requested by an internal
        or external signal."""
        yield None, 'the interrupt request source is an input port.'
        yield (re.compile(r'[a-zA-Z][a-zA-Z0-9_]*'),
               'the interrupt request source is the internal signal with the '
               'given name. The arrayness of the signal must match this '
               'interrupt\'s repetition. Level-sensitive interrupts cannot be '
               'associated with strobe signals.')

    @choice
    def active():
        """This key specifies the event that the interrupt is sensitive to."""
        yield 'high', 'the interrupt is level/strobe-sensitive, active-high.'
        yield 'low', 'the interrupt is level/strobe-sensitive, active-low.'
        yield 'rising', 'the interrupt is rising-edge sensitive.'
        yield 'falling', 'the interrupt is falling-edge sensitive.'
        yield 'edge', 'the interrupt is sensitive to any edge.'

    @choice
    def group():
        """The interrupt request port for the internal signal can optionally be
        grouped along with other ports in a record. This key specifies the name
        of the group record."""
        yield None, 'port grouping is determined by the global default.'
        yield False, 'the port is not grouped in a record.'
        yield (re.compile(r'[a-zA-Z][a-zA-Z0-9_]*'),
               'the port is grouped in a record with the specified name.')
