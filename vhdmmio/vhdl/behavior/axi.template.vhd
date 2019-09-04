|$block PRE
  |@ Complete the AXI stream handshakes that occurred in the previous cycle for
  |@ field $fd.name$.
  |$if b.bus.can_write()
    |if $s2m[i]$.aw.ready = '1' then
    |  $state[i]$.aw.valid := '0';
    |end if;
    |if $s2m[i]$.w.ready = '1' then
    |  $state[i]$.w.valid := '0';
    |end if;
    |if $state[i]$.b.valid = '0' then
    |  $state[i]$.b := $s2m[i]$.b;
    |end if;
  |$endif
  |$if b.bus.can_read()
    |if $s2m[i]$.ar.ready = '1' then
    |  $state[i]$.ar.valid := '0';
    |end if;
    |if $state[i]$.r.valid = '0' then
    |  $state[i]$.r := $s2m[i]$.r;
    |end if;
  |$endif
  |
  |$if b.interrupt_internal is not None
    |@ Connect the incoming interrupt signal for field $fd.name$
    |@ to the associated internal signal.
    |$if b.interrupt_internal.width is None
      |$b.interrupt_internal.drive_name$ := $s2m[i]$.u.irq;
    |$else
      |$b.interrupt_internal.drive_name$($i$) := $s2m[i]$.u.irq;
    |$endif
  |$endif
|$endblock

|$block READ_REQ
  |if $state[i]$.ar.valid = '0' then
  |  $state[i]$.ar.addr := X"00000000";
  |  $state[i]$.ar.addr($b.subaddress_range$) := $w_sub$;
  |  $state[i]$.ar.prot := r_prot;
  |  $state[i]$.ar.valid := '1';
  |  r_defer := true;
  |elsif r_req then
  |  r_block := true;
  |end if;
|$endblock

|$block READ_RESP
  |if $state[i]$.r.valid = '1' then
  |  $r_data$ := $state[i]$.r.data;
  |  case $state[i]$.r.resp is
  |    when AXI4L_RESP_OKAY => r_ack := true;
  |    when AXI4L_RESP_DECERR => null;
  |    when others => r_nack := true;
  |  end case;
  |  $state[i]$.r.valid := '0';
  |else
  |  r_block := true;
  |end if;
|$endblock

|$block WRITE_REQ
  |if $state[i]$.aw.valid = '0' and $state[i]$.w.valid = '0' then
  |  $state[i]$.aw.addr := X"00000000";
  |  $state[i]$.aw.addr($b.subaddress_range$) := $w_sub$;
  |  $state[i]$.aw.prot := w_prot;
  |  $state[i]$.aw.valid := '1';
  |
  |  $state[i]$.w.data := $w_data$;
  |  for i in 0 to $width//8-1$ loop
  |    $state[i]$.w.strb(i) := $w_strobe$(i*8);
  |  end loop;
  |  $state[i]$.w.valid := '1';
  |
  |  w_defer := true;
  |elsif w_req then
  |  w_block := true;
  |end if;
|$endblock

|$block WRITE_RESP
  |if $state[i]$.b.valid = '1' then
  |  case $state[i]$.b.resp is
  |    when AXI4L_RESP_OKAY => w_ack := true;
  |    when AXI4L_RESP_DECERR => null;
  |    when others => w_nack := true;
  |  end case;
  |  $state[i]$.b.valid := '0';
  |else
  |  w_block := true;
  |end if;
|$endblock

|$block POST
  |@ Handle reset for field $fd.name$.
  |if reset = '1' then
    |$if b.bus.can_write()
    |  $state[i]$.aw.valid := '0';
    |  $state[i]$.w.valid := '0';
    |  $state[i]$.b.valid := '0';
    |$endif
    |$if b.bus.can_read()
    |  $state[i]$.ar.valid := '0';
    |  $state[i]$.r.valid := '0';
    |$endif
  |end if;
  |
  |@ Assign output ports for field $fd.name$.
  |$if b.bus.can_write()
    |$m2s[i]$.aw <= $state[i]$.aw;
    |$m2s[i]$.w <= $state[i]$.w;
    |$m2s[i]$.b.ready <= not $state[i]$.b.valid;
  |$else
    |$m2s[i]$.aw <= AXI4LA_RESET;
    |$m2s[i]$.w <= AXI4LW$width$_RESET;
    |$m2s[i]$.b <= AXI4LH_RESET;
  |$endif
  |$if b.bus.can_read()
    |$m2s[i]$.ar <= $state[i]$.ar;
    |$m2s[i]$.r.ready <= not $state[i]$.r.valid;
  |$else
    |$m2s[i]$.ar <= AXI4LA_RESET;
    |$m2s[i]$.r <= AXI4LH_RESET;
  |$endif
|$endblock
