-- Generated using vhdMMIO $version$ (https://github.com/abs-tudelft/vhdmmio)

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

      -- Clock sensitive to the rising edge and synchronous, active-$e.reset_active$ reset.
      $e.clock_name$ : in std_logic;
      $e.reset_name$ : in std_logic := '$'0' if e.reset_active == 'high' else '1'$';

$     PORTS

      -- AXI4-lite + interrupt request bus to the master.
$if e.bus_flatten
      $e.bus_prefix$awvalid : in  std_logic := '0';
      $e.bus_prefix$awready : out std_logic := '1';
      $e.bus_prefix$awaddr  : in  std_logic_vector(31 downto 0) := X"00000000";
      $e.bus_prefix$awprot  : in  std_logic_vector(2 downto 0) := "000";
      $e.bus_prefix$wvalid  : in  std_logic := '0';
      $e.bus_prefix$wready  : out std_logic := '1';
      $e.bus_prefix$wdata   : in  std_logic_vector($bw-1$ downto 0) := (others => '0');
      $e.bus_prefix$wstrb   : in  std_logic_vector($bw//8-1$ downto 0) := (others => '0');
      $e.bus_prefix$bvalid  : out std_logic := '0';
      $e.bus_prefix$bready  : in  std_logic := '1';
      $e.bus_prefix$bresp   : out std_logic_vector(1 downto 0) := "00";
      $e.bus_prefix$arvalid : in  std_logic := '0';
      $e.bus_prefix$arready : out std_logic := '1';
      $e.bus_prefix$araddr  : in  std_logic_vector(31 downto 0) := X"00000000";
      $e.bus_prefix$arprot  : in  std_logic_vector(2 downto 0) := "000";
      $e.bus_prefix$rvalid  : out std_logic := '0';
      $e.bus_prefix$rready  : in  std_logic := '1';
      $e.bus_prefix$rdata   : out std_logic_vector($bw-1$ downto 0) := (others => '0');
      $e.bus_prefix$rresp   : out std_logic_vector(1 downto 0) := "00";
      $e.bus_prefix$uirq    : out std_logic := '0'
$else
      $e.bus_prefix$i : in  axi4l$bw$_m2s_type := AXI4L$bw$_M2S_RESET;
      $e.bus_prefix$o : out axi4l$bw$_s2m_type := AXI4L$bw$_S2M_RESET
$endif

    );
  end component;

end package $r.name$_pkg;

$if defined('PACKAGE_BODY')
package body $r.name$_pkg is

$ PACKAGE_BODY

end package body $r.name$_pkg;
$endif
