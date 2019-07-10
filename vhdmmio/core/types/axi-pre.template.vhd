@ Complete the AXI stream handshakes that occurred in the previous cycle for
@ field $l.field_descriptor.meta.name$.
$if l.write_caps is not None
if $s2m[i]$.aw.ready = '1' then
  $state[i]$.aw.valid := '0';
end if;
if $s2m[i]$.w.ready = '1' then
  $state[i]$.w.valid := '0';
end if;
if $state[i]$.b.valid = '0' then
  $state[i]$.b := $s2m[i]$.b;
end if;
$endif
$if l.read_caps is not None
if $s2m[i]$.ar.ready = '1' then
  $state[i]$.ar.valid := '0';
end if;
if $state[i]$.r.valid = '0' then
  $state[i]$.r := $s2m[i]$.r;
end if;
$endif

$if l.interrupt is not None
@ Connect the incoming interrupt signal for field $l.field_descriptor.meta.name$
@ to the associated internal signal.
$if l.interrupt.width is None
$l.interrupt.drive_name$ := $s2m[i]$.u.irq;
$else
$l.interrupt.drive_name$($i$) := $s2m[i]$.u.irq;
$endif
$endif
