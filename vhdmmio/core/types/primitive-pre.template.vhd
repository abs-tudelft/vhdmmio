$if l.get_ctrl('invalidate')
@ Handle invalidation control input.
if $invalidate[i]$ = '1' then
$if vec
  $state[i].d$@:= (others => '0');
$else
  $state[i].d$@:= '0';
$endif
  $state[i].v$@:= '0';
end if;
$endif

$if l.get_ctrl('ready')
@ Handle ready control input.
if $ready[i]$ = '1' then
$if vec
  $state[i].d$@:= (others => '0');
$else
  $state[i].d$@:= '0';
$endif
  $state[i].v$@:= '0';
end if;
$endif

$if l.get_ctrl('clear')
@ Handle clear control input.
if $clear[i]$ = '1' then
$if vec
  $state[i].d$@:= (others => '0');
$else
  $state[i].d$@:= '0';
$endif
end if;
$endif

$if l.after_bus_write == 'invalidate'
@ Handle post-write invalidation one cycle after the write occurs.
if $state[i].inval$ = '1' then
$if vec
  $state[i].d$@:= (others => '0');
$else
  $state[i].d$@:= '0';
$endif
  $state[i].v$@:= '0';
end if;
$state[i].inval$@:= '0';
$endif

$if l.hw_write != 'disabled'
@ Handle hardware write for field $l.field_descriptor.meta.name$: $l.hw_write$.
$if l.after_hw_write != 'nothing'
@ Also handle post-write operation: $l.after_hw_write$.
$endif
$if l.hw_write == 'status'
$state[i].d$@:= $write_data[i]$;
$state[i].v$@:= '1';
$else
$if l.hw_write == 'stream'
if $valid[i]$ = '1' and $state[i].v$ = '0' then
  $state[i].d$@:= $data[i]$;
$else
if $write_enable[i]$ = '1' then
$endif
$if l.hw_write == 'enabled'
  $state[i].d$@:= $write_data[i]$;
$endif
$if l.hw_write == 'accumulate'
$if vec
  $state[i].d$@:= std_logic_vector(unsigned($state[i].d$)@+ unsigned($write_data[i]$));
$else
  $state[i].d$@:= $state[i].d$@xor $write_data[i]$;
$endif
$endif
$if l.hw_write == 'subtract'
$if vec
  $state[i].d$@:= std_logic_vector(unsigned($state[i].d$)@- unsigned($write_data[i]$));
$else
  $state[i].d$@:= $state[i].d$@xor $write_data[i]$;
$endif
$endif
$if l.hw_write == 'set'
  $state[i].d$@:= $state[i].d$@or $write_data[i]$;
$endif
$if l.hw_write == 'reset'
  $state[i].d$@:= $state[i].d$@and not $write_data[i]$;
$endif
$if l.hw_write == 'toggle'
  $state[i].d$@:= $state[i].d$@xor $write_data[i]$;
$endif
$if l.after_hw_write == 'validate'
  $state[i].v$@:= '1';
$endif
end if;
$endif
$endif

$if l.get_ctrl('validate')
@ Handle validation control input.
if $validate[i]$ = '1' then
  $state[i].v$@:= '1';
end if;
$endif

$if l.get_ctrl('increment')
@ Handle increment control input.
if $increment[i]$ = '1' then
$if vec
  $state[i].d$@:= std_logic_vector(unsigned($state[i].d$) + 1);
$else
  $state[i].d$@:= not $state[i].d$;
$endif
end if;
$endif

$if l.get_ctrl('decrement')
@ Handle decrement control input.
if $decrement[i]$ = '1' then
$if vec
  $state[i].d$@:= std_logic_vector(unsigned($state[i].d$) - 1);
$else
  $state[i].d$@:= not $state[i].d$;
$endif
end if;
$endif

$if l.get_ctrl('bit-set')
@ Handle bit set control input.
$state[i].d$@:= $state[i].d$@or $bit_set[i]$;
$endif

$if l.get_ctrl('bit-clear')
@ Handle bit clear control input.
$state[i].d$@:= $state[i].d$@and not $bit_clear[i]$;
$endif

$if l.get_ctrl('bit-toggle')
@ Handle bit toggle control input.
$state[i].d$@:= $state[i].d$@and xor $bit_toggle[i]$;
$endif

$if l.monitor_internal is not None
@ Handle monitoring internal signal.
$if l.monitor_mode == 'status'
$state[i].d$@:= $l.monitor_internal.use_name$;
$endif
$if l.monitor_mode == 'bit-set'
$state[i].d$@:= $state[i].d$@or $l.monitor_internal.use_name$;
$endif
$if l.monitor_mode == 'increment'
$if l.monitor_internal.width is None
if $l.monitor_internal.use_name$ = '1' then
$else
if $l.monitor_internal.use_name$($i$) = '1' then
$endif
  $state[i].d$@:= std_logic_vector(unsigned($state[i].d$) + 1);
end if;
$endif
$endif
