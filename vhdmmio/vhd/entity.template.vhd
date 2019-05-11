-- Generated using vhdMMIO (https://github.com/jvanstraten/vhdmmio)

library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_misc.all;
use ieee.numeric_std.all;

library work;
use work.vhdmmio_pkg.all;
use work.$NAME$_pkg.all;

entity $NAME$ is
  port (
    -- Clock sensitive to the rising edge and synchronous, active-high reset.
    clk   : in  std_logic;
    reset : in  std_logic := '0';

$   PORTS
    -- AXI4-lite + interrupt request bus to the master.
    bus_i : in  axi4l$DATA_WIDTH$_m2s_type := AXI4L$DATA_WIDTH$_M2S_RESET;
    bus_o : out axi4l$DATA_WIDTH$_s2m_type := AXI4L$DATA_WIDTH$_S2M_RESET

  );
end $NAME$;

architecure behavioral of $NAME$ is
begin
  reg_proc: process (clk) is

    -- Bus response output register.
    variable bus_v : axi4l$DATA_WIDTH$_s2m_type := AXI4L$DATA_WIDTH$_S2M_RESET;

    -- Holding registers for the AXI4-lite request channels. Having these
    -- allows us to make the accompanying ready signals register outputs
    -- without sacrificing a cycle's worth of delay for every transaction.
    variable awl : axi4la_type := AXI4LA_RESET;
    variable wl  : axi4lw$DATA_WIDTH$_type := AXI4LW$DATA_WIDTH$_RESET;
    variable arl : axi4la_type := AXI4LA_RESET;

    -- Request flags for the register logic. When asserted, a request is
    -- present in awl/wl/arl.
    variable w_req : boolean := false;
    variable r_req : boolean := false;

    -- Block flags for the register logic. This flag should be asserted when
    -- the respective request *can* be handled by the slave, but not yet.
    variable w_block : boolean := false;
    variable r_block : boolean := false;

$if N_IRQ > 0
    -- Interrupt registers. The interrupt output is asserted if flag & mask
    -- is nonzero. flags are asserted by hardware by means of incoming strobe
    -- signals when the respective enab bit is set, or by software through
    -- trigger fields, and are cleared by software through flag fields. The
    -- enable and mask fields are controlled through software only. They
    -- default and reset to 0 when such a field is present, or are constant
    -- high if not. flags always reset to 0.
    variable i_mask : std_logic_vector($N_IRQ - 1$ downto 0) := $IRQ_MASK_RESET$;
    variable i_flag : std_logic_vector($N_IRQ - 1$ downto 0) := (others => '0');
    variable i_enab : std_logic_vector($N_IRQ - 1$ downto 0) := $IRQ_ENAB_RESET$;

$endif
$   FIELD_VARIABLES
  begin
    if rising_edge(clk) then

      -------------------------------------------------------------------------
      -- Finish up the previous cycle
      -------------------------------------------------------------------------
      -- Invalidate responses that were acknowledged by the master in the
      -- previous cycle.
      if bus_i.b.ready = '1' then
        bus_v.b.valid := '0';
      end if;
      if bus_i.r.ready = '1' then
        bus_v.r.valid := '0';
      end if;

      -- If we indicated to the master that we were ready for a transaction on
      -- any of the incoming channels, we must latch any incoming requests. If
      -- we're ready but there is no incoming request this becomes don't-care.
      if bus_v.aw.ready = '1' then
        awl := bus_i.aw;
      end if;
      if bus_v.w.ready = '1' then
        wl := bus_i.w;
      end if;
      if bus_v.ar.ready = '1' then
        arl := bus_i.ar;
      end if;

      -------------------------------------------------------------------------
      -- Set default values for the next cycle
      -------------------------------------------------------------------------
      -- Reset variables that shouldn't become registers to default values.
      w_req := false;
      r_req := false;
      w_block := false;
      r_block := false;

      -------------------------------------------------------------------------
      -- Handle interrupts
      -------------------------------------------------------------------------
$if N_IRQ > 0
      -- Assert the interrupt flags when the incoming strobe signals are
      -- asserted and the respective enable bits are set. Flags that do not
      -- have an accompanying field for clearing them are always overridden
      -- with the incoming signal, flags that do have a software clear field
      -- are OR'd.
$     IRQ_FLAG_LOGIC

      -- Set the outgoing interrupt flag if any flag/mask combo is active.
      bus_v.u.irq := or_reduce(i_mask and i_flag);
$else
      -- No incoming interrupts; request signal is always released.
      bus_v.u.irq := '0';
$endif

      -------------------------------------------------------------------------
      -- Handle MMIO fields
      -------------------------------------------------------------------------
      -- We're ready for a write/read when all the respective channels (or
      -- their holding registers) are ready/waiting for us.
      if awl.valid = '1' and wl.valid = '1' and bus_v.b.valid = '0' then
        w_req := true;
        bus_v.b.resp := AXI4L_RESP_OKAY;
      end if;
      if arl.valid = '1' and bus_v.r.valid = '0' then
        r_req := true;
        bus_v.r.data := X"00000000";
        bus_v.r.resp := AXI4L_RESP_OKAY;
      end if;

      -- The logic for the generated code for fields is as follows:
      --  - Write requests are to be handled when w_req is true. The request
      --    information is to be taken from awl and wl. When a field is
      --    addressed, it must do exactly one of the following:
      --     - Set the w_block flag to delay the transaction; the request will
      --       be held until the next cycle. Note that blocking fields cannot
      --       coexist with other blocking fields or volatile fields.
      --     - Set bus_v.b.valid to '1' and bus_v.b.resp to AXI4L_RESP_SLVERR
      --       or AXI4L_RESP_DECERR to send an error response.
      --     - Set bus_v.b.valid to '1' to indicate OK.
      --  - Read requests are to be handled when r_req is true. The request
      --    information is to be taken from arl. When a field is addressed, it
      --    must do exactly one of the following:
      --     - Set the r_block flag to delay the transaction; the request will
      --       be held until the next cycle. Note that blocking fields cannot
      --       coexist with other blocking fields or volatile fields.
      --     - Set bus_v.r.valid to '1' and bus_v.r.resp to AXI4L_RESP_SLVERR
      --       or AXI4L_RESP_DECERR to send an error response.
      --     - Set bus_v.r.valid to '1' and the appropriate bits in
      --       bus_v.r.data to the read result to indicate OK.
      -- The blocks below are auto-generated for the fields requested by the
      -- user.

$     FIELD_LOGIC
      -- If neither block nor valid was asserted for a requested write/read,
      -- send a decode error.
      if w_req and not w_block and bus_v.b.valid = '0' then
        bus_v.b.valid := '1';
        bus_v.b.resp := AXI4L_RESP_DECERR;
      end if;
      if r_req and not r_block and bus_v.r.valid = '0' then
        bus_v.r.valid := '1';
        bus_v.r.resp := AXI4L_RESP_DECERR;
      end if;

      -- When a request is acknowledged, invalidate the holding registers that
      -- stored the request to prepare them for the next one.
      if bus_v.b.valid = '1' then
        awl.valid := '0';
        wl.valid := '0';
      end if;
      if bus_v.r.valid = '1' then
        arl.valid := '0';
      end if;

      -- Mark the incoming channels as ready when their respective holding
      -- registers are empty.
      bus_v.aw.ready := not awl.valid;
      bus_v.w.ready := not wl.valid;
      bus_v.ar.ready := not arl.valid;

      -------------------------------------------------------------------------
      -- Handle AXI4-lite bus reset
      -------------------------------------------------------------------------
      -- Reset overrides everything, so it comes last. Note that field
      -- registers are *not* reset here; this would complicate code generation.
      -- Instead, the generated field logic blocks include reset logic for the
      -- field-specific registers.
      if reset = '1' then
        bus_v  := AXI4L$DATA_WIDTH$_S2M_RESET;
        awl    := AXI4LA_RESET;
        wl     := AXI4LW$DATA_WIDTH$_RESET;
        arl    := AXI4LA_RESET;
$if N_IRQ > 0
        i_mask := $IRQ_MASK_RESET$;
        i_flag := (others => '0');
        i_enab := $IRQ_ENAB_RESET$;
$endif
      end if;

      bus_o <= bus_v;

    end if;
  end process;
end behavioral;
