# Interrupt descriptors

In addition to MMIO, `vhdmmio` can handle interrupt routing for you.
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
vendor-specific, therefore they are not included in vhdmmio.

## Configuration keys

This structure supports the following configuration keys.

## `repeat`

This value specifies whether this interrupt descriptor describes a
single interrupt or an array of interrupts.

The following values are supported:

 - `null` (default): the descriptor describes a single interrupt.

 - an integer above or equal to 1: the descriptor describes an array of interrupts of the given size.

This key is optional unless required by context. If not specified, the default value (`null`) is used.

## Metadata keys

This configuration structure is used to name and document the
interrupt.

More information about this structure may be found [here](metadataconfig.md).

The following configuration keys are used to configure this structure.

### `mnemonic`

This key is documented [here](metadataconfig.md#mnemonic).

### `name`

This key is documented [here](metadataconfig.md#name).

### `brief`

This key is documented [here](metadataconfig.md#brief).

### `doc`

This key is documented [here](metadataconfig.md#doc).

## `internal`

This key specifies whether the interrupt is requested by an internal
or external signal.

The following values are supported:

 - `null` (default): the interrupt request source is an input port.

 - a string matching `[a-zA-Z][a-zA-Z0-9_]*`: the interrupt request source is the internal signal with the given name. The arrayness of the signal must match this interrupt's repetition. Level-sensitive interrupts cannot be associated with strobe signals.

This key is optional unless required by context. If not specified, the default value (`null`) is used.

## `active`

This key specifies the event that the interrupt is sensitive to.

The following values are supported:

 - `high` (default): the interrupt is level/strobe-sensitive, active-high.

 - `low`: the interrupt is level/strobe-sensitive, active-low.

 - `rising`: the interrupt is rising-edge sensitive.

 - `falling`: the interrupt is falling-edge sensitive.

 - `edge`: the interrupt is sensitive to any edge.

This key is optional unless required by context. If not specified, the default value (`high`) is used.

## Interface keys

These keys specify how the VHDL entity interface is generated.

More information about this structure may be found [here](interfaceconfig.md).

The following configuration keys are used to configure this structure.

### `group`

This key is documented [here](interfaceconfig.md#group).

### `flatten`

This key is documented [here](interfaceconfig.md#flatten).

### `generic-group`

This key is documented [here](interfaceconfig.md#generic-group).

### `generic-flatten`

This key is documented [here](interfaceconfig.md#generic-flatten).