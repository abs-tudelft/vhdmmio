"""Submodule for `EntityConfig` configurable."""

import re
from ..configurable import configurable, Configurable, choice, choice_default

@configurable(name='VHDL entity configuration')
class EntityConfig(Configurable):
    """This configuration structure can be used to configure the common
    interfaces of the generated entity, such as the bus and the clock."""
    #pylint: disable=E0211,E0213

    @choice_default('clk')
    def clock_name():
        """This key specifies the name of the clock input port. The clock is
        always rising-edge-sensitive."""
        yield (re.compile(r'[a-zA-Z][a-zA-Z0-9_]*'),
               'name of the clock input port.')

    @choice_default('reset')
    def reset_name():
        """This key specifies the name of the reset input port. The reset input
        is always synchronous, but can be set to either active-high or
        active-low using the `reset-active` parameter. The default `reset` name
        can only be used when the reset is active-high due to limitations in
        the template; it is suggested to suffix an `n` when the reset signal is
        active-low to avoid this problem."""
        yield (re.compile(r'[a-zA-Z][a-zA-Z0-9_]*'),
               'name of the reset input port.')

    @choice
    def reset_active():
        """This key specifies for which signal level the reset signal is
        considered to be asserted."""
        yield 'high', 'the reset signal is active-high.'
        yield ('low', 'the reset signal is active-low. The default `reset` '
               'port name cannot be used.')

    @choice_default('bus_')
    def bus_prefix():
        """This key specifies the prefix used for the AXI4-lite bus signals,
        including underscore separator if one is desired. When the bus is not
        flattened, the signals `<prefix>i` and `<prefix>o` are generated. When
        flattened, the standard names for the AXI4-lite interface channels are
        suffixed:

         - Write address channel: `awvalid`, `awready`, `awaddr` and `awprot`;
         - Write data channel: `wvalid`, `wready`, `wdata`, and `wstrb`;
         - Write response channel: `bvalid`, `bready`, and `bresp`;
         - Read address channel: `arvalid`, `arready`, `araddr`, and `arprot`;
         - Read data channel: `rvalid`, `rready`, `rdata`, and `rresp`.
        """
        yield (re.compile(r'[a-zA-Z][a-zA-Z0-9_]*'),
               'prefix for the bus ports.')

    @choice
    def bus_flatten():
        """This key specifies whether records or flattened signals are desired
        for the bus interface."""
        yield (False, 'the bus is not flattened; the records from '
               '`vhdmmio_pkg.vhd` are used.')
        yield (True, 'the bus is flattened; the standard AXI4-lite signal '
               'names are used.')
