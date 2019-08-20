-- Generated using vhdMMIO (https://github.com/abs-tudelft/vhdmmio)

library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_misc.all;
use ieee.numeric_std.all;

library work;
use work.vhdmmio_pkg.all;

package $r.name$_pkg is

$ PACKAGE

  -- Component declaration for $r.name$.
  component $r.name$ is
$if defined('GENERICS')
    generic (

$     GENERICS

    );
$endif
    port (
      -- Clock sensitive to the rising edge and synchronous, active-high reset.
      clk   : in  std_logic;
      reset : in  std_logic := '0';

$     PORTS

      -- AXI4-lite + interrupt request bus to the master.
      bus_i : in  axi4l$bw$_m2s_type := AXI4L$bw$_M2S_RESET;
      bus_o : out axi4l$bw$_s2m_type := AXI4L$bw$_S2M_RESET

    );
  end component;

end package $r.name$_pkg;

$if defined('PACKAGE_BODY')
package body $r.name$_pkg is

$ PACKAGE_BODY

end package body $r.name$_pkg;
$endif
