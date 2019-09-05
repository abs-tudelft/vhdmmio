-- Generated using vhdMMIO $version$ (https://github.com/abs-tudelft/vhdmmio)

library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_misc.all;
use ieee.numeric_std.all;

library work;
use work.vhdmmio_pkg.all;
use work.$r.name$_pkg.all;

entity $r.name$ is
$if defined('GENERICS')
  generic (

$   GENERICS

  );
$endif
  port (

    -- Clock sensitive to the rising edge and synchronous, active-$e.reset_active$ reset.
    $e.clock_name$ : in std_logic;
    $e.reset_name$ : in std_logic := '$'0' if e.reset_active == 'high' else '1'$';

$   PORTS

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
end $r.name$;

architecture behavioral of $r.name$ is
begin
  reg_proc: process ($e.clock_name$) is

    -- Convenience function for unsigned accumulation with differing vector
    -- widths.
    procedure accum_add(
      accum: inout std_logic_vector;
      addend: std_logic_vector) is
    begin
      accum := std_logic_vector(
        unsigned(accum) + resize(unsigned(addend), accum'length));
    end procedure accum_add;

    -- Convenience function for unsigned subtraction with differing vector
    -- widths.
    procedure accum_sub(
      accum: inout std_logic_vector;
      addend: std_logic_vector) is
    begin
      accum := std_logic_vector(
        unsigned(accum) - resize(unsigned(addend), accum'length));
    end procedure accum_sub;

$if e.reset_name != 'reset'
    -- Internal alias for the reset input.
    variable reset : std_logic;
$endif

    -- Bus response output register.
    variable bus_v : axi4l$bw$_s2m_type := AXI4L$bw$_S2M_RESET; -- reg

    -- Holding registers for the AXI4-lite request channels. Having these
    -- allows us to make the accompanying ready signals register outputs
    -- without sacrificing a cycle's worth of delay for every transaction.
    variable awl : axi4la_type := AXI4LA_RESET; -- reg
    variable wl  : axi4lw$bw$_type := AXI4LW$bw$_RESET; -- reg
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

$if di.write_count
    -- Write response request flag and tag for deferred requests. When the flag
    -- is set, the register matching the tag can return its result.
    variable w_rreq : boolean := false;
    variable w_rtag : std_logic_vector($di.write_width-1$ downto 0);

    -- Write tag FIFO.
    type w_tag_array is array (natural range <>) of std_logic_vector($di.write_width-1$ downto 0);
    variable w_tags     : w_tag_array(0 to $2**di.tag_depth_log2-1$); -- mem
    variable w_tag_wptr : std_logic_vector($di.tag_depth_log2-1$ downto 0) := (others => '0'); -- reg;
    variable w_tag_rptr : std_logic_vector($di.tag_depth_log2-1$ downto 0) := (others => '0'); -- reg;
    variable w_tag_cnt  : std_logic_vector($di.tag_depth_log2$ downto 0) := (others => '0'); -- reg;
$endif

$if di.read_count
    -- Read response request flag and tag for deferred requests. When the flag
    -- is set, the register matching the tag can return its result.
    variable r_rreq : boolean := false;
    variable r_rtag : std_logic_vector($di.read_width-1$ downto 0);

    -- Read tag FIFO.
    type r_tag_array is array (natural range <>) of std_logic_vector($di.read_width-1$ downto 0);
    variable r_tags     : r_tag_array(0 to $2**di.tag_depth_log2-1$); -- mem
    variable r_tag_wptr : std_logic_vector($di.tag_depth_log2-1$ downto 0) := (others => '0'); -- reg;
    variable r_tag_rptr : std_logic_vector($di.tag_depth_log2-1$ downto 0) := (others => '0'); -- reg;
    variable r_tag_cnt  : std_logic_vector($di.tag_depth_log2$ downto 0) := (others => '0'); -- reg;
$endif

    -- Request signals. w_strb is a validity bit for each data bit; it actually
    -- always has byte granularity but encoding it this way makes the code a
    -- lot nicer (and it should be optimized to the same thing by any sane
    -- synthesizer).
    variable w_addr : std_logic_vector($ai.width-1$ downto 0);
    variable w_data : std_logic_vector($bw-1$ downto 0) := (others => '0');
    variable w_strb : std_logic_vector($bw-1$ downto 0) := (others => '0');
$if r.need_prot
    variable w_prot : std_logic_vector(2 downto 0) := (others => '0'); -- reg
$else
    constant w_prot : std_logic_vector(2 downto 0) := (others => '0');
$endif
    variable r_addr : std_logic_vector($ai.width-1$ downto 0);
$if r.need_prot
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
$if di.write_count
    variable w_defer : boolean := false;
    variable w_dtag  : std_logic_vector($di.write_width-1$ downto 0);
$endif
$if di.read_count
    variable r_defer : boolean := false;
    variable r_dtag  : std_logic_vector($di.read_width-1$ downto 0);
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
    variable r_hold  : std_logic_vector($r.get_max_logical_read_width()-1$ downto 0) := (others => '0'); -- reg

    -- Physical read data. This is taken from r_hold based on which physical
    -- subregister is being read.
    variable r_data  : std_logic_vector($bw-1$ downto 0);

$if ii.concat_width > 0
    -- Interrupt input variables. i_raw is set to the raw incoming interrupt
    -- values, as read by the interrupt-raw fields. This value is subsequently
    -- converted to i_req by the generated interrupt logic; an interrupt is
    -- considered active when i_req is asserted high. i_raw can also be used to
    -- form a state register if it is used before it is assigned to do edge
    -- detection. It is not reset to anything, so the edge detection logic
    -- should only ever spuriously detect an edge after the device is powered
    -- on. Therefore, as long as the register file is appropriately reset
    -- before use, there should be no spurious detections.
    variable i_raw   : std_logic_vector($ii.concat_width - 1$ downto 0) := "$'0' * ii.concat_width$"; -- (reg)
    variable i_req   : std_logic_vector($ii.concat_width - 1$ downto 0) := "$'0' * ii.concat_width$";

    -- Interrupt registers. The interrupt output is asserted if flag & umsk
    -- is nonzero. If an interrupt flag clearing field is available, flags are
    -- asserted by hardware by means of an incoming signal when the respective
    -- enab bit is set, or by software through trigger fields, and are cleared
    -- by software through the clear field. If there is no clear field, the
    -- interrupt is level-sensitive (mutually exclusive with the pend field).
    -- The enable and mask fields are controlled through software only. They
    -- default and reset to 0 when such a field is present, or are constant
    -- high if not. flags always reset to 0.
    variable i_umsk  : std_logic_vector($ii.concat_width - 1$ downto 0) := "$ii.umsk_reset$"; -- reg
    variable i_flag  : std_logic_vector($ii.concat_width - 1$ downto 0) := "$'0' * ii.concat_width$"; -- reg
    variable i_enab  : std_logic_vector($ii.concat_width - 1$ downto 0) := "$ii.enab_reset$"; -- reg

$endif
$   DECLARATIONS
  begin
    if rising_edge($e.clock_name$) then

      -- Reset variables that shouldn't become registers to default values.
$if e.reset_name != 'reset'
 |$if e.reset_active == 'high'
      reset   := $e.reset_name$;
 |$else
      reset   := not $e.reset_name$;
 |$endif
$endif
      w_req   := false;
      r_req   := false;
      w_lreq  := false;
      r_lreq  := false;
$if di.write_count
      w_rreq  := false;
      w_rtag  := (others => '0');
$endif
$if di.read_count
      r_rreq  := false;
      r_rtag  := (others => '0');
$endif
      w_addr  := (others => '0');
      w_data  := (others => '0');
      w_strb  := (others => '0');
      r_addr  := (others => '0');
$if di.write_count
      w_defer := false;
      w_dtag  := (others => '0');
$endif
$if di.read_count
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
$if ii.concat_width > 0
      i_req   := (others => '0');
$endif

      -------------------------------------------------------------------------
      -- Finish up the previous cycle
      -------------------------------------------------------------------------
      -- Invalidate responses that were acknowledged by the master in the
      -- previous cycle.
$if e.bus_flatten
      if $e.bus_prefix$bready = '1' then
$else
      if $e.bus_prefix$i.b.ready = '1' then
$endif
        bus_v.b.valid := '0';
      end if;
$if e.bus_flatten
      if $e.bus_prefix$rready = '1' then
$else
      if $e.bus_prefix$i.r.ready = '1' then
$endif
        bus_v.r.valid := '0';
      end if;

      -- If we indicated to the master that we were ready for a transaction on
      -- any of the incoming channels, we must latch any incoming requests. If
      -- we're ready but there is no incoming request this becomes don't-care.
      if bus_v.aw.ready = '1' then
$if e.bus_flatten
        awl.valid := $e.bus_prefix$awvalid;
        awl.addr  := $e.bus_prefix$awaddr;
        awl.prot  := $e.bus_prefix$awprot;
$else
        awl := $e.bus_prefix$i.aw;
$endif
      end if;
      if bus_v.w.ready = '1' then
$if e.bus_flatten
        wl.valid := $e.bus_prefix$wvalid;
        wl.data  := $e.bus_prefix$wdata;
        wl.strb  := $e.bus_prefix$wstrb;
$else
        wl := $e.bus_prefix$i.w;
$endif
      end if;
      if bus_v.ar.ready = '1' then
$if e.bus_flatten
        arl.valid := $e.bus_prefix$arvalid;
        arl.addr  := $e.bus_prefix$araddr;
        arl.prot  := $e.bus_prefix$arprot;
$else
        arl := $e.bus_prefix$i.ar;
$endif
      end if;

$if defined('INTERNAL_SIGNAL_EARLY')
      -------------------------------------------------------------------------
      -- Connect internal signal input/strobe ports
      -------------------------------------------------------------------------
$     INTERNAL_SIGNAL_EARLY
$endif

      -------------------------------------------------------------------------
      -- Handle interrupts
      -------------------------------------------------------------------------
$if ii.concat_width > 0
$     IRQ_LOGIC

      -- Always clear interrupt flags that cannot be cleared through a field.
      i_flag := i_flag and "$ii.strobe_mask$";

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

$if di.write_count
      -- Handle outstanding write requests.
      w_rtag := w_tags(to_integer(unsigned(w_tag_rptr)));
      if w_tag_cnt /= "0$'0'*di.tag_depth_log2$" then

        -- There are outstanding requests, so everything is a lookahead now.
        w_lreq := w_lreq or w_req;
        w_req := false;

        -- If there is room in the response register, request a response.
        if bus_v.b.valid = '0' then
          w_rreq := true;
        end if;

      elsif w_tag_cnt($di.tag_depth_log2$) = '1' then

        -- FIFO full; disable even lookaheads (since we wouldn't be able to do
        -- anything with the deferral tag if the lookahead can be deferred).
        w_req := false;
        w_lreq := false;

      end if;
$endif

$if di.read_count
      -- Handle outstanding read requests.
      r_rtag := r_tags(to_integer(unsigned(r_tag_rptr)));
      if r_tag_cnt /= "0$'0'*di.tag_depth_log2$" then

        -- There are outstanding requests, so everything is a lookahead now.
        r_lreq := r_lreq or r_req;
        r_req := false;

        -- If there is room in the response register, request a response.
        if bus_v.b.valid = '0' then
          r_rreq := true;
        end if;

      elsif r_tag_cnt($di.tag_depth_log2$) = '1' then

        -- FIFO full; disable even lookaheads (since we wouldn't be able to do
        -- anything with the deferral tag if the lookahead can be deferred).
        r_req := false;
        r_lreq := false;

      end if;
$endif

$if r.harden
      -- Security: if the incoming request is interrupting a multi-word
      -- register access made by a higher-security master, block it until all
      -- outstanding requests are done and then send an error response.
      if w_multi = '1' and (
        (awl.prot(0) = '0' and w_prot(0) = '1') or (awl.prot(1) = '1' and w_prot(1) = '0')
      ) then
        if w_req then
          bus_v.b.valid := '1';
          bus_v.b.resp := AXI4L_RESP_SLVERR;
          awl.valid := '0';
          wl.valid := '0';
        end if;
        w_lreq := false;
        w_req := false;
      end if;
      if r_multi = '1' and (
        (arl.prot(0) = '0' and r_prot(0) = '1') or (arl.prot(1) = '1' and r_prot(1) = '0')
      ) then
        if r_req then
          bus_v.r.valid := '1';
          bus_v.r.resp := AXI4L_RESP_SLVERR;
          bus_v.r.data := (others => '0');
          arl.valid := '0';
        end if;
        r_lreq := false;
        r_req := false;
      end if;
$endif

      -- Capture request inputs into more consistently named variables.
$if r.need_prot
      if w_req then
        w_prot := awl.prot;
      end if;
$endif
$if not defined('WRITE_ADDR_CONCAT')
      w_addr := awl.addr;
$else
      w_addr(31 downto 0) := awl.addr;
      if bus_v.aw.ready = '1' then
$       WRITE_ADDR_CONCAT
      end if;
$endif
      for b in w_strb'range loop
        w_strb(b) := wl.strb(b / 8);
      end loop;
      w_data := wl.data and w_strb;
$if r.need_prot
      if r_req then
        r_prot := arl.prot;
      end if;
$endif
$if not defined('READ_ADDR_CONCAT')
      r_addr := arl.addr;
$else
      r_addr(31 downto 0) := arl.addr;
      if bus_v.ar.ready = '1' then
$       READ_ADDR_CONCAT
      end if;
$endif

$if defined('FIELD_LOGIC_BEFORE')
      -------------------------------------------------------------------------
      -- Generated field logic
      -------------------------------------------------------------------------
$     FIELD_LOGIC_BEFORE
$endif

$if defined('FIELD_LOGIC_READ') or di.read_count
      -------------------------------------------------------------------------
      -- Bus read logic
      -------------------------------------------------------------------------
$     FIELD_LOGIC_READ

 |$if di.read_count
      -- Handle deferred reads.
      if r_rreq then
$       FIELD_LOGIC_READ_TAG
      end if;
 |$endif
$endif

$if defined('FIELD_LOGIC_WRITE') or di.write_count
      -------------------------------------------------------------------------
      -- Bus write logic
      -------------------------------------------------------------------------
$     FIELD_LOGIC_WRITE

 |$if di.write_count
      -- Handle deferred writes.
      if w_rreq then
$       FIELD_LOGIC_WRITE_TAG
      end if;
 |$endif
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
$if di.write_count
      if (w_req and not w_block) or w_defer then

        -- Accept write requests by invalidating the request holding
        -- registers.
        awl.valid := '0';
        wl.valid := '0';

      end if;

      if w_defer then
        assert w_req or w_lreq severity failure;

        -- Defer the write: push the register tag into the FIFO...
        w_tags(to_integer(unsigned(w_tag_wptr))) := w_dtag;
        w_tag_wptr := std_logic_vector(unsigned(w_tag_wptr) + 1);
        w_tag_cnt := std_logic_vector(unsigned(w_tag_cnt) + 1);

      end if;

      if w_rreq and not w_block then

        -- Complete deferred write by popping the tag FIFO.
        w_tag_rptr := std_logic_vector(unsigned(w_tag_rptr) + 1);
        w_tag_cnt := std_logic_vector(unsigned(w_tag_cnt) - 1);

      end if;

      if (w_rreq or (w_req and not w_defer)) and not w_block then
$else
      if w_req and not w_block then

        -- Accept write requests by invalidating the request holding
        -- registers.
        awl.valid := '0';
        wl.valid := '0';
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

      end if;

      -- Perform the read action dictated by the field logic.
$if di.read_count
      if (r_req and not r_block) or r_defer then

        -- Accept read requests by invalidating the request holding
        -- registers.
        arl.valid := '0';

      end if;

      if r_defer then
        assert r_req or r_lreq severity failure;

        -- Defer the read: push the register tag into the FIFO...
        r_tags(to_integer(unsigned(r_tag_wptr))) := r_dtag;
        r_tag_wptr := std_logic_vector(unsigned(r_tag_wptr) + 1);
        r_tag_cnt := std_logic_vector(unsigned(r_tag_cnt) + 1);

      end if;

      if r_rreq and not r_block then

        -- Complete deferred read by popping the tag FIFO.
        r_tag_rptr := std_logic_vector(unsigned(r_tag_rptr) + 1);
        r_tag_cnt := std_logic_vector(unsigned(r_tag_cnt) - 1);

      end if;

      if (r_rreq or (r_req and not r_defer)) and not r_block then
$else
      if r_req and not r_block then

        -- Accept read requests by invalidating the request holding
        -- registers.
        arl.valid := '0';
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

      end if;

$if r.harden
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

$if defined('INTERNAL_SIGNAL_LATE')
      -------------------------------------------------------------------------
      -- Internal signal logic
      -------------------------------------------------------------------------
$     INTERNAL_SIGNAL_LATE
$endif

      -------------------------------------------------------------------------
      -- Handle AXI4-lite bus reset
      -------------------------------------------------------------------------
      -- Reset overrides everything, so it comes last. Note that field
      -- registers are *not* reset here; this would complicate code generation.
      -- Instead, the generated field logic blocks include reset logic for the
      -- field-specific registers.
      if reset = '1' then
        bus_v      := AXI4L$bw$_S2M_RESET;
        awl        := AXI4LA_RESET;
        wl         := AXI4LW$bw$_RESET;
        arl        := AXI4LA_RESET;
$if di.write_count
        w_tag_wptr := (others => '0');
        w_tag_rptr := (others => '0');
        w_tag_cnt  := (others => '0');
$endif
$if di.read_count
        r_tag_wptr := (others => '0');
        r_tag_rptr := (others => '0');
        r_tag_cnt  := (others => '0');
$endif
        w_hstb     := (others => '0');
        w_hold     := (others => '0');
$if r.need_prot
        w_prot     := (others => '0');
        r_prot     := (others => '0');
$endif
        w_multi    := '0';
        r_multi    := '0';
        r_hold     := (others => '0');
$if ii.concat_width > 0
        i_umsk     := "$ii.umsk_reset$";
        i_flag     := "$'0' * ii.concat_width$";
        i_enab     := "$ii.enab_reset$";
$endif
      end if;

$if e.bus_flatten
      $e.bus_prefix$awready <= bus_v.aw.ready;
      $e.bus_prefix$wready  <= bus_v.w.ready;
      $e.bus_prefix$bvalid  <= bus_v.b.valid;
      $e.bus_prefix$bresp   <= bus_v.b.resp;
      $e.bus_prefix$arready <= bus_v.ar.ready;
      $e.bus_prefix$rvalid  <= bus_v.r.valid;
      $e.bus_prefix$rdata   <= bus_v.r.data;
      $e.bus_prefix$rresp   <= bus_v.r.resp;
      $e.bus_prefix$uirq    <= bus_v.u.irq;
$else
      $e.bus_prefix$o <= bus_v;
$endif

    end if;
  end process;
end behavioral;
