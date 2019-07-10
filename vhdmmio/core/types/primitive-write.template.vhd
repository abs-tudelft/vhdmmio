$block AFTER_WRITE
$if l.after_bus_write != 'nothing'
@ Handle post-write operation: $l.after_bus_write$.
$endif
$if l.after_bus_write == 'validate'
$state[i].v$@:= '1';
$endif
$if l.after_bus_write == 'invalidate'
$state[i].v$@:= '1';
$state[i].inval$@:= '1';
$endif
$endblock

$block HANDLE_WRITE
$if l.overflow_internal is not None
if $state[i].v$ = '1' then
$if l.overflow_internal.width is None
$l.overflow_internal.drive_name$ := '1';
$else
$l.overflow_internal.drive_name$($i$) := '1';
$endif
end if;
$endif
$if l.bus_write == 'error'
w_nack@:= true;
$endif
$if l.bus_write == 'invalid-wait'
if $state[i].v$ = '1' then
  w_block@:= true;
else
  $state[i].d$@:= $w_data$;
  w_ack@:= true;
$ AFTER_WRITE
end if;
$endif
$if l.bus_write == 'invalid-only'
if $state[i].v$ = '1' then
  w_nack@:= true;
else
  $state[i].d$@:= $w_data$;
  w_ack@:= true;
$ AFTER_WRITE
end if;
$endif
$if l.bus_write == 'invalid'
if $state[i].v$ = '0' then
  $state[i].d$@:= $w_data$;
end if;
w_ack@:= true;
$AFTER_WRITE
$endif
$if l.bus_write == 'enabled'
$state[i].d$@:= $w_data$;
w_ack@:= true;
$AFTER_WRITE
$endif
$if l.bus_write == 'masked'
$state[i].d$@:= ($state[i].d$ and not $w_strobe$)@or $w_data$;
w_ack@:= true;
$AFTER_WRITE
$endif
$if l.bus_write == 'accumulate'
$if vec
$state[i].d$@:= std_logic_vector(unsigned($state[i].d$)@+ unsigned($w_data$));
$else
$state[i].d$@:= $state[i].d$@xor $w_data$;
$endif
w_ack@:= true;
$AFTER_WRITE
$endif
$if l.bus_write == 'subtract'
$if vec
$state[i].d$@:= std_logic_vector(unsigned($state[i].d$)@- unsigned($w_data$));
$else
$state[i].d$@:= $state[i].d$@xor $w_data$;
$endif
w_ack@:= true;
$AFTER_WRITE
$endif
$if l.bus_write == 'bit-set'
$state[i].d$@:= $state[i].d$@or $w_data$;
w_ack@:= true;
$AFTER_WRITE
$endif
$if l.bus_write == 'bit-clear'
$state[i].d$@:= $state[i].d$@and not $w_data$;
w_ack@:= true;
$AFTER_WRITE
$endif
$if l.bus_write == 'bit-toggle'
$state[i].d$@:= $state[i].d$@xor $w_data$;
w_ack@:= true;
$AFTER_WRITE
$endif
$endblock

$if l.bus_write != 'disabled'
@ Write mode: $l.bus_write$.
$if l.get_ctrl('lock')
if $lock[i]$ = '0' then
$ HANDLE_WRITE
end if;
$else
$HANDLE_WRITE
$endif
$endif
