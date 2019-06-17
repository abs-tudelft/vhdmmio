-- Generated using vhdMMIO (https://github.com/abs-tudelft/vhdmmio)

library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_misc.all;
use ieee.numeric_std.all;

library work;
use work.vhdmmio_pkg.all;

package $r.meta.name$_pkg is

  -- Component declaration for $r.meta.name$.
  component $r.meta.name$ is
$if defined('GENERICS')
    generic (

$     GENERICS

      -- This is just here to make generation easier; prevents errors when no
      -- generics are needed.
      SENTINEL_DO_NOT_USE : boolean := false

    );
$endif
    port (
      -- Clock sensitive to the rising edge and synchronous, active-high reset.
      clk   : in  std_logic;
      reset : in  std_logic := '0';

$     PORTS

      -- AXI4-lite + interrupt request bus to the master.
      bus_i : in  axi4l$r.bus_width$_m2s_type := AXI4L$r.bus_width$_M2S_RESET;
      bus_o : out axi4l$r.bus_width$_s2m_type := AXI4L$r.bus_width$_S2M_RESET

    );
  end component;

$ PACKAGE

end package $r.meta.name$_pkg;

$if defined('PACKAGE_BODY')
package body $r.meta.name$_pkg is

$ PACKAGE_BODY

end package body $r.meta.name$_pkg;
$endif
