@ Handle reset for field $l.field_descriptor.meta.name$.
if reset = '1' then
$if l.write_caps is not None
  $state[i]$.aw.valid := '0';
  $state[i]$.w.valid := '0';
  $state[i]$.b.valid := '0';
$endif
$if l.read_caps is not None
  $state[i]$.ar.valid := '0';
  $state[i]$.r.valid := '0';
$endif
end if;

@ Assign output ports for field $l.field_descriptor.meta.name$.
$if l.write_caps is not None
$m2s[i]$.aw <= $state[i]$.aw;
$m2s[i]$.w <= $state[i]$.w;
$m2s[i]$.b.ready <= not $state[i]$.b.valid;
$else
$m2s[i]$.aw <= AXI4LA_RESET;
$m2s[i]$.w <= AXI4LW$width$_RESET;
$m2s[i]$.b <= AXI4LH_RESET;
$endif
$if l.read_caps is not None
$m2s[i]$.ar <= $state[i]$.ar;
$m2s[i]$.r.ready <= not $state[i]$.r.valid;
$else
$m2s[i]$.ar <= AXI4LA_RESET;
$m2s[i]$.r <= AXI4LH_RESET;
$endif
