$if l.hw_write != 'status'
@ Handle reset for field $l.field_descriptor.meta.name$.
$if l.get_ctrl('reset')
@ This includes the optional per-field reset control signal.
if reset = '1' or $reset[i]$ = '1' then
$else
if reset = '1' then
$endif
  $state[i].d$@:= $reset_data if isinstance(reset_data, str) else reset_data[i]$;
  $state[i].v$@:= $reset_valid$;
$if l.after_bus_write == 'invalidate'
  $state[i].inval$@:= '0';
$endif
end if;
$endif

$if l.hw_read in ('simple', 'enabled')
@ Assign the read outputs for field $l.field_descriptor.meta.name$.
$data[i]$ <= $state[i].d$;
$if l.hw_read == 'enabled'
$valid[i]$ <= $state[i].v$;
$endif
$endif

$if l.hw_read == 'handshake'
@ Assign the ready output for field $l.field_descriptor.meta.name$.
$ready[i]$ <= not $state[i].v$;
$endif

$if l.drive_internal is not None
@ Assign the internal signal for field $l.field_descriptor.meta.name$.
$l.drive_internal.drive_name$ := $state[i].d$;
$endif
