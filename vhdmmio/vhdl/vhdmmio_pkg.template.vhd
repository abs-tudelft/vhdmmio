-- Generated using vhdMMIO $version$ (https://github.com/abs-tudelft/vhdmmio)

library ieee;
use ieee.std_logic_1164.all;

package vhdmmio_pkg is

  -- Protection codes.
  constant AXI4L_PROT_UNPR: std_logic_vector(0 downto 0) := "0";
  constant AXI4L_PROT_PRIV: std_logic_vector(0 downto 0) := "1";
  constant AXI4L_PROT_SECU: std_logic_vector(1 downto 1) := "0";
  constant AXI4L_PROT_NSEC: std_logic_vector(1 downto 1) := "1";
  constant AXI4L_PROT_DATA: std_logic_vector(2 downto 2) := "0";
  constant AXI4L_PROT_INSN: std_logic_vector(2 downto 2) := "1";
  constant AXI4L_PROT_DEFAULT: std_logic_vector(2 downto 0) :=
    AXI4L_PROT_DATA & AXI4L_PROT_SECU & AXI4L_PROT_UNPR;

  -- Response codes.
  constant AXI4L_RESP_OKAY: std_logic_vector(1 downto 0) := "00";
  constant AXI4L_RESP_SLVERR: std_logic_vector(1 downto 0) := "10";
  constant AXI4L_RESP_DECERR: std_logic_vector(1 downto 0) := "11";

  -- Read/write request channel, master to slave.
  type axi4la_type is record
    valid : std_logic;
    addr  : std_logic_vector(31 downto 0);
    prot  : std_logic_vector(2 downto 0);
  end record;

  constant AXI4LA_RESET: axi4la_type := (
    valid => '0',
    addr  => X"00000000",
    prot  => AXI4L_PROT_DEFAULT
  );

  -- Write data channel, 32-bit, master to slave.
  type axi4lw32_type is record
    valid : std_logic;
    data  : std_logic_vector(31 downto 0);
    strb  : std_logic_vector(3 downto 0);
  end record;

  constant AXI4LW32_RESET: axi4lw32_type := (
    valid => '0',
    data  => X"00000000",
    strb  => "0000"
  );

  -- Write data channel, 64-bit, master to slave.
  type axi4lw64_type is record
    valid : std_logic;
    data  : std_logic_vector(63 downto 0);
    strb  : std_logic_vector(7 downto 0);
  end record;

  constant AXI4LW64_RESET: axi4lw64_type := (
    valid => '0',
    data  => X"00000000_00000000",
    strb  => "00000000"
  );

  -- Write response channel, slave to master.
  type axi4lb_type is record
    valid : std_logic;
    resp  : std_logic_vector(1 downto 0);
  end record;

  constant AXI4LB_RESET: axi4lb_type := (
    valid => '0',
    resp  => AXI4L_RESP_OKAY
  );

  -- Read response channel, 32-bit, slave to master.
  type axi4lr32_type is record
    valid : std_logic;
    data  : std_logic_vector(31 downto 0);
    resp  : std_logic_vector(1 downto 0);
  end record;

  constant AXI4LR32_RESET: axi4lr32_type := (
    valid => '0',
    data  => X"00000000",
    resp  => AXI4L_RESP_OKAY
  );

  -- Read response channel, 64-bit, slave to master.
  type axi4lr64_type is record
    valid : std_logic;
    data  : std_logic_vector(63 downto 0);
    resp  : std_logic_vector(1 downto 0);
  end record;

  constant AXI4LR64_RESET: axi4lr64_type := (
    valid => '0',
    data  => X"00000000_00000000",
    resp  => AXI4L_RESP_OKAY
  );

  -- Handshake return for any AXI4-lite channel.
  type axi4lh_type is record
    ready : std_logic;
  end record;

  constant AXI4LH_RESET: axi4lh_type := (
    ready => '1'
  );

  -- User-defined channel used for interrupt signalling passing along with all
  -- vhdMMIO AXI4-lite busses.
  type axi4lu_type is record
    irq   : std_logic;
  end record;

  constant AXI4LU_RESET: axi4lu_type := (
    irq   => '0'
  );

  -- Complete 32-bit AXI4-lite bus, master to slave direction.
  type axi4l32_m2s_type is record
    aw    : axi4la_type;
    w     : axi4lw32_type;
    b     : axi4lh_type;
    ar    : axi4la_type;
    r     : axi4lh_type;
  end record;

  constant AXI4L32_M2S_RESET: axi4l32_m2s_type := (
    aw    => AXI4LA_RESET,
    w     => AXI4LW32_RESET,
    b     => AXI4LH_RESET,
    ar    => AXI4LA_RESET,
    r     => AXI4LH_RESET
  );

  type axi4l32_m2s_array is array (natural range <>) of axi4l32_m2s_type;

  -- Complete 32-bit AXI4-lite bus, slave to master direction.
  type axi4l32_s2m_type is record
    aw    : axi4lh_type;
    w     : axi4lh_type;
    b     : axi4lb_type;
    ar    : axi4lh_type;
    r     : axi4lr32_type;
    u     : axi4lu_type;
  end record;

  constant AXI4L32_S2M_RESET: axi4l32_s2m_type := (
    aw    => AXI4LH_RESET,
    w     => AXI4LH_RESET,
    b     => AXI4LB_RESET,
    ar    => AXI4LH_RESET,
    r     => AXI4LR32_RESET,
    u     => AXI4LU_RESET
  );

  type axi4l32_s2m_array is array (natural range <>) of axi4l32_s2m_type;

  -- Complete 64-bit AXI4-lite bus, master to slave direction.
  type axi4l64_m2s_type is record
    aw    : axi4la_type;
    w     : axi4lw64_type;
    b     : axi4lh_type;
    ar    : axi4la_type;
    r     : axi4lh_type;
  end record;

  constant AXI4L64_M2S_RESET: axi4l64_m2s_type := (
    aw    => AXI4LA_RESET,
    w     => AXI4LW64_RESET,
    b     => AXI4LH_RESET,
    ar    => AXI4LA_RESET,
    r     => AXI4LH_RESET
  );

  type axi4l64_m2s_array is array (natural range <>) of axi4l64_m2s_type;

  -- Complete 64-bit AXI4-lite bus, slave to master direction.
  type axi4l64_s2m_type is record
    aw      : axi4lh_type;
    w       : axi4lh_type;
    b       : axi4lb_type;
    ar      : axi4lh_type;
    r       : axi4lr64_type;
    u       : axi4lu_type;
  end record;

  constant AXI4L64_S2M_RESET: axi4l64_s2m_type := (
    aw    => AXI4LH_RESET,
    w     => AXI4LH_RESET,
    b     => AXI4LB_RESET,
    ar    => AXI4LH_RESET,
    r     => AXI4LR64_RESET,
    u     => AXI4LU_RESET
  );

  type axi4l64_s2m_array is array (natural range <>) of axi4l64_s2m_type;

  -- Arrays of primitive types, occasionally used by the register file
  -- generator. Note that std_logic_array is defined just like
  -- std_logic_vector; the difference is that the programmer can assume that
  -- *_array types have ascending ranges, while std_logic_vector is used with
  -- descending ranges.
  type std_logic_array is array (natural range <>) of std_logic;
  type boolean_array is array (natural range <>) of boolean;
  type natural_array is array (natural range <>) of natural;

end package vhdmmio_pkg;
