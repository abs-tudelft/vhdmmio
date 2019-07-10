$block AFTER_READ
$if l.after_bus_read != 'nothing'
@ Handle post-read operation: $l.after_bus_read$.
$endif
$if l.after_bus_read in ['invalidate', 'clear']
$if vec
$state[i].d$@:= (others => '0');
$else
$state[i].d$@:= '0';
$endif
$endif
$if l.after_bus_read == 'invalidate'
$state[i].v$@:= '0';
$endif
$if l.after_bus_read == 'increment'
$if vec
$state[i].d$@:= std_logic_vector(unsigned($state[i].d$) + 1);
$else
$state[i].d$@:= not $state[i].d$;
$endif
$endif
$if l.after_bus_read == 'decrement'
$if vec
$state[i].d$@:= std_logic_vector(unsigned($state[i].d$) - 1);
$else
$state[i].d$@:= not $state[i].d$;
$endif
$endif
$endblock

$if l.bus_read != 'disabled'
@ Read mode: $l.bus_read$.
$endif
$if l.bus_read == 'error'
r_nack@:= true;
$endif
$if l.underflow_internal is not None
if $state[i].v$ = '0' then
$if l.underflow_internal.width is None
$l.underflow_internal := '1';
$else
$l.underflow_internal($i$) := '1';
$endif
end if;
$endif
$if l.bus_read in ['enabled', 'valid-wait', 'valid-only']
$r_data$@:= $state[i].d$;
$if l.bus_read in ['valid-wait', 'valid-only']
if $state[i].v$ = '1' then
  r_ack@:= true;
$ AFTER_READ
else
$if l.bus_read in ['valid-wait']
  r_block@:= true;
$else
  r_nack@:= true;
$endif
end if;
$else
r_ack@:= true;
$AFTER_READ
$endif
$endif
