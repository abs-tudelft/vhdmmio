-- Generated using vhdMMIO (https://github.com/abs-tudelft/vhdmmio)

library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_misc.all;
use ieee.numeric_std.all;

library work;
use work.vhdmmio_pkg.all;
use work.$r.meta.name$_pkg.all;

entity $r.meta.name$ is
$if defined('GENERICS')
  generic (

$   GENERICS

  );
$endif
  port (

    -- Clock sensitive to the rising edge and synchronous, active-high reset.
    clk   : in  std_logic;
    reset : in  std_logic := '0';

$   PORTS

    -- AXI4-lite + interrupt request bus to the master.
    bus_i : in  axi4l$r.bus_width$_m2s_type := AXI4L$r.bus_width$_M2S_RESET;
    bus_o : out axi4l$r.bus_width$_s2m_type := AXI4L$r.bus_width$_S2M_RESET

  );
end $r.meta.name$;

architecture behavioral of $r.meta.name$ is
begin
  reg_proc: process (clk) is

    -- Bus response output register.
    variable bus_v : axi4l$r.bus_width$_s2m_type := AXI4L$r.bus_width$_S2M_RESET; -- reg

    -- Holding registers for the AXI4-lite request channels. Having these
    -- allows us to make the accompanying ready signals register outputs
    -- without sacrificing a cycle's worth of delay for every transaction.
    variable awl : axi4la_type := AXI4LA_RESET; -- reg
    variable wl  : axi4lw$r.bus_width$_type := AXI4LW$r.bus_width$_RESET; -- reg
    variable arl : axi4la_type := AXI4LA_RESET; -- reg

    -- Request flags for the register logic. When asserted, a request is
    -- present in awl/wl/arl, and the response can be returned immediately.
    -- This is used by simple registers.
    variable w_req : boolean := false;
    variable r_req : boolean := false;

    -- As above, but asserted when there is a request that can NOT be returned
    -- immediately for whatever reason, but CAN be started already if deferral
    -- is supported by the targeted block. Abbreviation for lookahead request.
    -- Note that *_lreq implies *_req.
    variable w_lreq : boolean := false;
    variable r_lreq : boolean := false;

$if r.write_tag_count
    -- Write response request flag and tag for deferred requests. When the flag
    -- is set, the register matching the tag can return its result.
    variable w_rreq : boolean := false;
    variable w_rtag : std_logic_vector($r.write_tag_width-1$ downto 0);

    -- Write tag FIFO.
    type w_tag_array is array (natural range <>) of std_logic_vector($r.write_tag_width-1$ downto 0);
    variable w_tags     : w_tag_array(0 to $2**r.tag_depth_log2-1$); -- mem
    variable w_tag_wptr : std_logic_vector($r.tag_depth_log2-1$ downto 0) := (others => '0'); -- reg;
    variable w_tag_rptr : std_logic_vector($r.tag_depth_log2-1$ downto 0) := (others => '0'); -- reg;
    variable w_tag_cnt  : std_logic_vector($r.tag_depth_log2$ downto 0) := (others => '0'); -- reg;
$endif

$if r.read_tag_count
    -- Read response request flag and tag for deferred requests. When the flag
    -- is set, the register matching the tag can return its result.
    variable r_rreq : boolean := false;
    variable r_rtag : std_logic_vector($r.read_tag_width-1$ downto 0);

    -- Read tag FIFO.
    type r_tag_array is array (natural range <>) of std_logic_vector($r.read_tag_width-1$ downto 0);
    variable r_tags     : r_tag_array(0 to $2**r.tag_depth_log2-1$); -- mem
    variable r_tag_wptr : std_logic_vector($r.tag_depth_log2-1$ downto 0) := (others => '0'); -- reg;
    variable r_tag_rptr : std_logic_vector($r.tag_depth_log2-1$ downto 0) := (others => '0'); -- reg;
    variable r_tag_cnt  : std_logic_vector($r.tag_depth_log2$ downto 0) := (others => '0'); -- reg;
$endif

    -- Request signals. w_strb is a validity bit for each data bit; it actually
    -- always has byte granularity but encoding it this way makes the code a
    -- lot nicer (and it should be optimized to the same thing by any sane
    -- synthesizer).
    variable w_addr : std_logic_vector(31 downto 0);
    variable w_data : std_logic_vector($r.bus_width-1$ downto 0) := (others => '0');
    variable w_strb : std_logic_vector($r.bus_width-1$ downto 0) := (others => '0');
$if r.secure
    variable w_prot : std_logic_vector(2 downto 0) := (others => '0'); -- reg
$else
    constant w_prot : std_logic_vector(2 downto 0) := (others => '0');
$endif
    variable r_addr : std_logic_vector(31 downto 0);
$if r.secure
    variable r_prot : std_logic_vector(2 downto 0) := (others => '0'); -- reg
$else
    constant r_prot : std_logic_vector(2 downto 0) := (others => '0');
$endif

    -- Logical write data holding registers. For multi-word registers, write
    -- data is held in w_hold and w_hstb until the last subregister is written,
    -- at which point their entire contents are written at once.
    variable w_hold : std_logic_vector($r.get_max_logical_write_width()-1$ downto 0) := (others => '0'); -- reg
    variable w_hstb : std_logic_vector($r.get_max_logical_write_width()-1$ downto 0) := (others => '0'); -- reg

    -- Between the first and last access to a multiword register, the multi
    -- bit will be set. If it is set while a request with a different *_prot is
    -- received, the interrupting request is rejected if it is A) non-secure
    -- while the interrupted request is secure or B) unprivileged while the
    -- interrupted request is privileged. If it is not rejected, previously
    -- buffered data is cleared and masked. Within the same security level, it
    -- is up to the bus master to not mess up its own access pattern. The last
    -- access to a multiword register clears the bit; for the read end r_hold
    -- is also cleared in this case to prevent data leaks.
    variable w_multi : std_logic := '0'; -- reg
    variable r_multi : std_logic := '0'; -- reg

    -- Response flags. When *_req is set and *_addr matches a register, it must
    -- set at least one of these flags; when *_rreq is set and *_rtag matches a
    -- register, it must also set at least one of these, except it cannot set
    -- *_defer. A decode error can be generated by intentionally NOT setting
    -- any of these flags, but this should only be done by registers that
    -- contain only one field (usually, these would be AXI-lite passthrough
    -- "registers"). The action taken by the non-register-specific logic is as
    -- follows (priority decoder):
    --
    --  - if *_defer is set, push *_dtag into the deferal FIFO;
    --  - if *_block is set, do nothing;
    --  - otherwise, if *_nack is set, send a slave error response;
    --  - otherwise, if *_ack is set, send a positive response;
    --  - otherwise, send a decode error response.
    --
    -- In addition to the above, the request stream(s) will be handshaked if
    -- *_req was set and a response is sent or the response is deferred.
    -- Likewise, the deferal FIFO will be popped if *_rreq was set and a
    -- response is sent.
    --
    -- The valid states can be summarized as follows:
    --
    -- .----------------------------------------------------------------------------------.
    -- | req | lreq | rreq || ack | nack | block | defer || request | response | defer    |
    -- |-----+------+------||-----+------+-------+-------||---------+----------+----------|
    -- |  0  |  0   |  0   ||  0  |  0   |   0   |   0   ||         |          |          | Idle.
    -- |-----+------+------||-----+------+-------+-------||---------+----------+----------|
    -- |  0  |  0   |  1   ||  0  |  0   |   0   |   0   ||         | dec_err  | pop      | Completing
    -- |  0  |  0   |  1   ||  1  |  0   |   0   |   0   ||         | ack      | pop      | previous,
    -- |  0  |  0   |  1   ||  -  |  1   |   0   |   0   ||         | slv_err  | pop      | no
    -- |  0  |  0   |  1   ||  -  |  -   |   1   |   0   ||         |          |          | lookahead.
    -- |-----+------+------||-----+------+-------+-------||---------+----------+----------|
    -- |  1  |  0   |  0   ||  0  |  0   |   0   |   0   || accept  | dec_err  |          | Responding
    -- |  1  |  0   |  0   ||  1  |  0   |   0   |   0   || accept  | ack      |          | immediately
    -- |  1  |  0   |  0   ||  -  |  1   |   0   |   0   || accept  | slv_err  |          | to incoming
    -- |  1  |  0   |  0   ||  -  |  -   |   1   |   0   ||         |          |          | request.
    -- |-----+------+------||-----+------+-------+-------||---------+----------+----------|
    -- |  1  |  0   |  0   ||  0  |  0   |   0   |   1   || accept  |          | push     | Deferring.
    -- |  0  |  1   |  0   ||  0  |  0   |   0   |   1   || accept  |          | push     | Deferring.
    -- |-----+------+------||-----+------+-------+-------||---------+----------+----------|
    -- |  0  |  1   |  1   ||  0  |  0   |   0   |   0   ||         | dec_err  | pop      | Completing
    -- |  0  |  1   |  1   ||  1  |  0   |   0   |   0   ||         | ack      | pop      | previous,
    -- |  0  |  1   |  1   ||  -  |  1   |   0   |   0   ||         | slv_err  | pop      | ignoring
    -- |  0  |  1   |  1   ||  -  |  -   |   1   |   0   ||         |          |          | lookahead.
    -- |-----+------+------||-----+------+-------+-------||---------+----------+----------|
    -- |  0  |  1   |  1   ||  0  |  0   |   0   |   1   || accept  | dec_err  | pop+push | Completing
    -- |  0  |  1   |  1   ||  1  |  0   |   0   |   1   || accept  | ack      | pop+push | previous,
    -- |  0  |  1   |  1   ||  -  |  1   |   0   |   1   || accept  | slv_err  | pop+push | deferring
    -- |  0  |  1   |  1   ||  -  |  -   |   1   |   1   || accept  |          | push     | lookahead.
    -- '----------------------------------------------------------------------------------'
    --
    -- This can be simplified to the following:
    --
    -- .----------------------------------------------------------------------------------.
    -- | req | lreq | rreq || ack | nack | block | defer || request | response | defer    |
    -- |-----+------+------||-----+------+-------+-------||---------+----------+----------|
    -- |  -  |  -   |  -   ||  -  |  -   |   1   |   -   ||         |          |          |
    -- |-----+------+------||-----+------+-------+-------||---------+----------+----------|
    -- |  -  |  -   |  1   ||  -  |  1   |   0   |   -   ||         | slv_err  | pop      |
    -- |  1  |  -   |  0   ||  -  |  1   |   0   |   -   || accept  | slv_err  |          |
    -- |-----+------+------||-----+------+-------+-------||---------+----------+----------|
    -- |  -  |  -   |  1   ||  1  |  0   |   0   |   -   ||         | ack      | pop      |
    -- |  1  |  -   |  0   ||  1  |  0   |   0   |   -   || accept  | ack      |          |
    -- |-----+------+------||-----+------+-------+-------||---------+----------+----------|
    -- |  -  |  -   |  1   ||  0  |  0   |   0   |   -   ||         | dec_err  | pop      |
    -- |  1  |  -   |  0   ||  0  |  0   |   0   |   -   || accept  | dec_err  |          |
    -- |-----+------+------||-----+------+-------+-------||---------+----------+----------|
    -- |  -  |  -   |  -   ||  -  |  -   |   -   |   1   || accept  |          | push     |
    -- '----------------------------------------------------------------------------------'
    --
$if r.write_tag_count
    variable w_defer : boolean := false;
    variable w_dtag  : std_logic_vector($r.write_tag_width-1$ downto 0);
$endif
$if r.read_tag_count
    variable r_defer : boolean := false;
    variable r_dtag  : std_logic_vector($r.read_tag_width-1$ downto 0);
$endif
    variable w_block : boolean := false;
    variable r_block : boolean := false;
    variable w_nack  : boolean := false;
    variable r_nack  : boolean := false;
    variable w_ack   : boolean := false;
    variable r_ack   : boolean := false;

    -- Logical read data holding register. This is set when r_ack is set during
    -- an access to the first physical register of a logical register for all
    -- fields in the logical register.
    variable r_hold : std_logic_vector($r.get_max_logical_read_width()-1$ downto 0) := (others => '0'); -- reg

    -- Physical read data. This is taken from r_hold based on which physical
    -- subregister is being read.
    variable r_data : std_logic_vector($r.bus_width-1$ downto 0);

$if r.interrupt_count > 0
    -- Interrupt registers. The interrupt output is asserted if flag & umsk
    -- is nonzero. If an interrupt flag clearing field is available, flags are
    -- asserted by hardware by means of an incoming signal when the respective
    -- enab bit is set, or by software through trigger fields, and are cleared
    -- by software through the clear field. If there is no clear field, the
    -- interrupt is level-sensitive (mutually exclusive with the pend field).
    -- The enable and mask fields are controlled through software only. They
    -- default and reset to 0 when such a field is present, or are constant
    -- high if not. flags always reset to 0.
    variable i_umsk : std_logic_vector($r.interrupt_count - 1$ downto 0) := "$r.get_interrupt_unmask_reset()$"; -- reg
    variable i_flag : std_logic_vector($r.interrupt_count - 1$ downto 0) := "$'0' * r.interrupt_count$"; -- reg
    variable i_enab : std_logic_vector($r.interrupt_count - 1$ downto 0) := "$r.get_interrupt_enable_reset()$"; -- reg
    variable i_req  : std_logic_vector($r.interrupt_count - 1$ downto 0) := "$'0' * r.interrupt_count$";

$endif
$   DECLARATIONS
  begin
    if rising_edge(clk) then

      -- Reset variables that shouldn't become registers to default values.
      w_req   := false;
      r_req   := false;
      w_lreq  := false;
      r_lreq  := false;
$if r.write_tag_count
      w_rreq  := false;
      w_rtag  := (others => '0');
$endif
$if r.read_tag_count
      r_rreq  := false;
      r_rtag  := (others => '0');
$endif
      w_addr  := (others => '0');
      w_data  := (others => '0');
      w_strb  := (others => '0');
      r_addr  := (others => '0');
$if r.write_tag_count
      w_defer := false;
      w_dtag  := (others => '0');
$endif
$if r.read_tag_count
      r_defer := false;
      r_dtag  := (others => '0');
$endif
      w_block := false;
      r_block := false;
      w_nack  := false;
      r_nack  := false;
      w_ack   := false;
      r_ack   := false;
      r_data  := (others => '0');
$if r.interrupt_count > 0
      i_req   := (others => '0');
$endif

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
      -- Handle interrupts
      -------------------------------------------------------------------------
$if r.interrupt_count > 0
$     IRQ_LOGIC

      -- Always clear interrupt flags that cannot be cleared through a field.
      i_flag := i_flag and "$r.get_interrupt_strobe_mask()$";

      -- Assert interrupt flags that are being requested and are enabled.
      i_flag := i_flag or (i_req and i_enab);

      -- Set the outgoing interrupt flag if any flag/mask combo is active.
      bus_v.u.irq := or_reduce(i_flag and i_umsk);
$else
      -- No incoming interrupts; request signal is always released.
      bus_v.u.irq := '0';
$endif

      -------------------------------------------------------------------------
      -- Handle MMIO fields
      -------------------------------------------------------------------------
      -- We're ready for a write/read when all the respective channels (or
      -- their holding registers) are ready/waiting for us.
      if awl.valid = '1' and wl.valid = '1' then
        if bus_v.b.valid = '0' then
          w_req := true; -- Request valid and response register empty.
        else
          w_lreq := true; -- Request valid, but response register is busy.
        end if;
      end if;
      if arl.valid = '1' then
        if bus_v.r.valid = '0' then
          r_req := true; -- Request valid and response register empty.
        else
          r_lreq := true; -- Request valid, but response register is busy.
        end if;
      end if;

$if r.write_tag_count
      -- Handle outstanding write requests.
      w_rtag := w_tags(to_integer(unsigned(w_tag_rptr)));
      if w_tag_cnt = "0$'0'*r.tag_depth_log2$" then

        -- There are outstanding requests, so everything is a lookahead now.
        w_lreq := w_lreq or w_req;
        w_req := false;

        -- If there is room in the response register, request a response.
        if bus_v.b.valid = '0' then
          w_rreq := true;
        end if;

      elsif w_tag_cnt($r.tag_depth_log2$) = '1' then

        -- FIFO full; disable even lookaheads (since we wouldn't be able to do
        -- anything with the deferral tag if the lookahead can be deferred).
        w_req := false;
        w_lreq := false;

      end if;
$endif

$if r.read_tag_count
      -- Handle outstanding read requests.
      r_rtag := r_tags(to_integer(unsigned(r_tag_rptr)));
      if r_tag_cnt = "0$'0'*r.tag_depth_log2$" then

        -- There are outstanding requests, so everything is a lookahead now.
        r_lreq := r_lreq or r_req;
        r_req := false;

        -- If there is room in the response register, request a response.
        if bus_v.b.valid = '0' then
          r_rreq := true;
        end if;

      elsif r_tag_cnt($r.tag_depth_log2$) = '1' then

        -- FIFO full; disable even lookaheads (since we wouldn't be able to do
        -- anything with the deferral tag if the lookahead can be deferred).
        r_req := false;
        r_lreq := false;

      end if;
$endif

$if r.secure
      -- Security: if the incoming request is interrupting a multi-word
      -- register access made by a higher-security master, block it until all
      -- outstanding requests are done and then send an error response.
      if w_multi = '1' and (
        (awl.prot(0) = '0' and w_prot(0) = '1') or (awl.prot(1) = '1' and w_prot(1) = '0')
      ) then
        if w_req then
          w_nack := true;
        end if;
        w_lreq := false;
        w_req := false;
      end if;
      if r_multi = '1' and (
        (arl.prot(0) = '0' and r_prot(0) = '1') or (arl.prot(1) = '1' and r_prot(1) = '0')
      ) then
        if r_req then
          r_nack := true;
        end if;
        r_lreq := false;
        r_req := false;
      end if;
$endif

      -- Capture request inputs into more consistently named variables.
$if r.secure
      if w_req then
        w_prot := awl.prot;
      end if;
$endif
      w_addr := awl.addr;
      for b in w_strb'range loop
        w_strb(b) := wl.strb(b / 8);
      end loop;
      w_data := wl.data and w_strb;
$if r.secure
      if r_req then
        r_prot := arl.prot;
      end if;
$endif
      r_addr := arl.addr;

$if defined('FIELD_LOGIC_BEFORE')
      -------------------------------------------------------------------------
      -- Generated field logic
      -------------------------------------------------------------------------
$     FIELD_LOGIC_BEFORE
$endif

      -------------------------------------------------------------------------
      -- Bus read logic
      -------------------------------------------------------------------------
$     FIELD_LOGIC_READ

$if r.read_tag_count
      -- Handle deferred reads.
      if r_rreq then
$       FIELD_LOGIC_READ_TAG
      end if;
$endif

      -------------------------------------------------------------------------
      -- Bus write logic
      -------------------------------------------------------------------------
$     FIELD_LOGIC_WRITE

$if r.write_tag_count
      -- Handle deferred writes.
$     FIELD_LOGIC_WRITE_TAG
$endif

$if defined('FIELD_LOGIC_AFTER')
      -------------------------------------------------------------------------
      -- Generated field logic
      -------------------------------------------------------------------------
$     FIELD_LOGIC_AFTER
$endif

      -------------------------------------------------------------------------
      -- Boilerplate bus access logic
      -------------------------------------------------------------------------
      -- Perform the write action dictated by the field logic.
$if r.write_tag_count
      if (w_rreq or w_req) and not w_block then
$else
      if w_req and not w_block then
$endif

        -- Send the appropriate write response.
        bus_v.b.valid := '1';
        if w_nack then
          bus_v.b.resp := AXI4L_RESP_SLVERR;
        elsif w_ack then
          bus_v.b.resp := AXI4L_RESP_OKAY;
        else
          bus_v.b.resp := AXI4L_RESP_DECERR;
        end if;

$if not r.write_tag_count
        -- Accept write requests by invalidating the request holding
        -- registers.
        awl.valid := '0';
        wl.valid := '0';
      end if;
$else
        if w_rreq then

          -- Complete deferred write by popping the tag FIFO.
          w_tag_rptr := std_logic_vector(unsigned(w_tag_rptr) + 1);
          w_tag_cnt := std_logic_vector(unsigned(w_tag_cnt) - 1);

        else
          assert w_req severity failure;

          -- Accept write requests by invalidating the request holding
          -- registers.
          awl.valid := '0';
          wl.valid := '0';

        end if;
      end if;

      -- Handle write deferral.
      if w_defer then
        assert w_req or w_lreq severity failure;

        -- Defer the write: push the register tag into the FIFO...
        w_tags(to_integer(unsigned(w_tag_wptr))) := w_dtag;
        w_tag_wptr := std_logic_vector(unsigned(w_tag_wptr) + 1);
        w_tag_cnt := std_logic_vector(unsigned(w_tag_cnt) + 1);

        -- ...and accept the request.
        awl.valid := '0';
        wl.valid := '0';

      end if;
$endif

      -- Perform the read action dictated by the field logic.
$if r.read_tag_count
      if (r_rreq or r_req) and not r_block then
$else
      if r_req and not r_block then
$endif

        -- Send the appropriate read response.
        bus_v.r.valid := '1';
        if r_nack then
          bus_v.r.resp := AXI4L_RESP_SLVERR;
        elsif r_ack then
          bus_v.r.resp := AXI4L_RESP_OKAY;
          bus_v.r.data := r_data;
        else
          bus_v.r.resp := AXI4L_RESP_DECERR;
        end if;

$if not r.read_tag_count
        -- Accept read requests by invalidating the request holding
        -- registers.
        arl.valid := '0';

      end if;
$else
        if r_rreq then

          -- Complete deferred read by popping the tag FIFO.
          r_tag_rptr := std_logic_vector(unsigned(r_tag_rptr) + 1);
          r_tag_cnt := std_logic_vector(unsigned(r_tag_cnt) - 1);

        else
          assert r_req severity failure;

          -- Accept read requests by invalidating the request holding
          -- registers.
          arl.valid := '0';

        end if;
      end if;

      -- Handle read deferral.
      if r_defer then
        assert r_req or r_lreq severity failure;

        -- Defer the read: push the register tag into the FIFO...
        r_tags(to_integer(unsigned(r_tag_wptr))) := r_dtag;
        r_tag_wptr := std_logic_vector(unsigned(r_tag_wptr) + 1);
        r_tag_cnt := std_logic_vector(unsigned(r_tag_cnt) + 1);

        -- ...and accept the request.
        arl.valid := '0';

      end if;
$endif

$if r.secure
      -- If this was the end of a multi-word access, clear the holding
      -- registers to prevent data leaks to less privileged masters.
      if w_multi = '0' then
        w_hold := (others => '0');
        w_hstb := (others => '0');
      end if;
      if r_multi = '0' then
        r_hold := (others => '0');
      end if;
$else
      -- If we're at the end of a multi-word write, clear the write strobe
      -- holding register to prevent previously written data from leaking into
      -- later partial writes.
      if w_multi = '0' then
        w_hstb := (others => '0');
      end if;
$endif

      -- Mark the incoming channels as ready when their respective holding
      -- registers are empty.
      bus_v.aw.ready := not awl.valid;
      bus_v.w.ready := not wl.valid;
      bus_v.ar.ready := not arl.valid;

$if defined('INTERNAL_SIGNAL_END')
      -------------------------------------------------------------------------
      -- Internal signal logic
      -------------------------------------------------------------------------
$     INTERNAL_SIGNAL_LOGIC
$endif

      -------------------------------------------------------------------------
      -- Handle AXI4-lite bus reset
      -------------------------------------------------------------------------
      -- Reset overrides everything, so it comes last. Note that field
      -- registers are *not* reset here; this would complicate code generation.
      -- Instead, the generated field logic blocks include reset logic for the
      -- field-specific registers.
      if reset = '1' then
        bus_v      := AXI4L$r.bus_width$_S2M_RESET;
        awl        := AXI4LA_RESET;
        wl         := AXI4LW$r.bus_width$_RESET;
        arl        := AXI4LA_RESET;
$if r.write_tag_count
        w_tag_wptr := (others => '0');
        w_tag_rptr := (others => '0');
        w_tag_cnt  := (others => '0');
$endif
$if r.read_tag_count
        r_tag_wptr := (others => '0');
        r_tag_rptr := (others => '0');
        r_tag_cnt  := (others => '0');
$endif
        w_hstb     := (others => '0');
        w_hold     := (others => '0');
$if r.secure
        w_prot     := (others => '0');
        r_prot     := (others => '0');
$endif
        w_multi    := '0';
        r_multi    := '0';
        r_hold     := (others => '0');
$if r.interrupt_count > 0
        i_umsk     := "$r.get_interrupt_unmask_reset()$";
        i_flag     := "$'0' * r.interrupt_count$";
        i_enab     := "$r.get_interrupt_enable_reset()$";
$endif
      end if;

      bus_o <= bus_v;

    end if;
  end process;
end behavioral;
