|$block PRE
  |$if accum
    |@ Clear accumulation register for field $fd.name$.
    |$state.a$@:= (others => '0');
  |$endif
  |$if b.cfg.ctrl_invalidate
    |@ Handle invalidation control input.
    |if $invalidate[i]$ = '1' then
      |$if vec
      |  $state.d$@:= (others => '0');
      |$else
      |  $state.d$@:= '0';
      |$endif
    |  $state.v$@:= '0';
    |end if;
  |$endif
  |$if b.cfg.ctrl_ready
    |@ Handle ready control input for field $fd.name$.
    |if $ready[i]$ = '1' then
      |$if vec
      |  $state.d$@:= (others => '0');
      |$else
      |  $state.d$@:= '0';
      |$endif
    |  $state.v$@:= '0';
    |end if;
  |$endif
  |$if b.cfg.ctrl_clear
    |@ Handle clear control input for field $fd.name$.
    |if $clear[i]$ = '1' then
      |$if vec
      |  $state.d$@:= (others => '0');
      |$else
      |  $state.d$@:= '0';
      |$endif
    |end if;
  |$endif
  |$if b.cfg.after_bus_write == 'invalidate'
    |@ Handle post-write invalidation for field $fd.name$ one cycle after the write occurs.
    |if $state.inval$ = '1' then
      |$if vec
      |  $state.d$@:= (others => '0');
      |$else
      |  $state.d$@:= '0';
      |$endif
    |  $state.v$@:= '0';
    |end if;
    |$state.inval$@:= '0';
  |$endif
  |$if b.cfg.hw_write != 'disabled'
    |@ Handle hardware write for field $fd.name$: $b.cfg.hw_write$.
    |$if b.cfg.after_hw_write != 'nothing'
      |@ Also handle post-write operation: $b.cfg.after_hw_write$.
    |$endif
    |$if b.cfg.hw_write == 'status'
      |$state.d$@:= $write_data[i]$;
      |$state.v$@:= '1';
    |$else
      |$if b.cfg.hw_write == 'stream'
        |if $valid[i]$ = '1' and $state.v$ = '0' then
        |  $state.d$@:= $data[i]$;
      |$else
        |if $write_enable[i]$ = '1' then
      |$endif
        |$if b.cfg.hw_write == 'enabled'
        |  $state.d$@:= $write_data[i]$;
        |$endif
        |$if b.cfg.hw_write == 'accumulate'
          |$if vec
          |  accum_add($state.a$, $write_data[i]$);
          |$else
          |  accum_add($state.a$, (0 downto 0 => $write_data[i]$));
          |$endif
        |$endif
        |$if b.cfg.hw_write == 'subtract'
          |$if vec
          |  accum_sub($state.a$, $write_data[i]$);
          |$else
          |  accum_sub($state.a$, (0 downto 0 => $write_data[i]$));
          |$endif
        |$endif
        |$if b.cfg.hw_write == 'set'
          |$if b.bit_overflow_internal is not None
            |$if vec
            |  if or_reduce($state.d$ and $write_data[i]$) = '1' then
            |$else
            |  if $state.d$ = '1' and $write_data[i]$ = '1' then
            |$endif
              |$if b.bit_overflow_internal.is_vector()
            |    $b.bit_overflow_internal.drive_name$($i$) := '1';
              |$else
            |    $b.bit_overflow_internal.drive_name$ := '1';
              |$endif
          |  end if;
          |$endif
        |  $state.d$@:= $state.d$@or $write_data[i]$;
        |$endif
        |$if b.cfg.hw_write == 'reset'
          |$if b.bit_underflow_internal is not None
            |$if vec
            |  if or_reduce($write_data[i]$ and not $state.d$) = '1' then
            |$else
            |  if $state.d$ = '0' and $write_data[i]$ = '1' then
            |$endif
              |$if b.bit_underflow_internal.is_vector()
            |    $b.bit_underflow_internal.drive_name$($i$) := '1';
              |$else
            |    $b.bit_underflow_internal.drive_name$ := '1';
              |$endif
          |  end if;
          |$endif
        |  $state.d$@:= $state.d$@and not $write_data[i]$;
        |$endif
        |$if b.cfg.hw_write == 'toggle'
        |  $state.d$@:= $state.d$@xor $write_data[i]$;
        |$endif
        |$if b.cfg.after_hw_write == 'validate'
        |  $state.v$@:= '1';
        |$endif
      |end if;
    |$endif
  |$endif
  |$if b.cfg.ctrl_validate
    |@ Handle validation control input for field $fd.name$.
    |if $validate[i]$ = '1' then
    |  $state.v$@:= '1';
    |end if;
  |$endif
  |$if b.cfg.ctrl_increment
    |@ Handle increment control input for field $fd.name$.
    |accum_add($state.a$, (0 downto 0 => $increment[i]$));
  |$endif
  |$if b.cfg.ctrl_decrement
    |@ Handle decrement control input for field $fd.name$.
    |accum_sub($state.a$, (0 downto 0 => $decrement[i]$));
  |$endif
  |$if b.cfg.ctrl_bit_set
    |@ Handle bit set control input for field $fd.name$.
    |$if b.bit_overflow_internal is not None
      |$if vec
        |if or_reduce($state.d$ and $bit_set[i]$) = '1' then
      |$else
        |if $state.d$ = '1' and $bit_set[i]$ = '1' then
      |$endif
        |$if b.bit_overflow_internal.is_vector()
        |  $b.bit_overflow_internal.drive_name$($i$) := '1';
        |$else
        |  $b.bit_overflow_internal.drive_name$ := '1';
        |$endif
      |end if;
    |$endif
    |$state.d$@:= $state.d$@or $bit_set[i]$;
  |$endif
  |$if b.cfg.ctrl_bit_clear
    |@ Handle bit clear control input for field $fd.name$.
    |$if b.bit_underflow_internal is not None
      |$if vec
        |if or_reduce($bit_clear[i]$ and not $state.d$) = '1' then
      |$else
        |if $state.d$ = '0' and $bit_clear[i]$ = '1' then
      |$endif
        |$if b.bit_underflow_internal.is_vector()
        |  $b.bit_underflow_internal.drive_name$($i$) := '1';
        |$else
        |  $b.bit_underflow_internal.drive_name$ := '1';
        |$endif
      |end if;
    |$endif
    |$state.d$@:= $state.d$@and not $bit_clear[i]$;
  |$endif
  |$if b.cfg.ctrl_bit_toggle
    |@ Handle bit toggle control input for field $fd.name$.
    |$state.d$@:= $state.d$@and xor $bit_toggle[i]$;
  |$endif
  |$if b.monitor_internal is not None
    |@ Handle monitoring internal signal for field $fd.name$.
    |$if b.cfg.monitor_mode == 'status'
      |$state.d$@:= $b.monitor_internal.use_name$;
    |$endif
    |$if b.cfg.monitor_mode == 'bit-set'
      |$if b.bit_overflow_internal is not None
        |$if vec
          |if or_reduce($state.d$ and $b.monitor_internal.use_name$) = '1' then
        |$else
          |if $state.d$ = '1' and $b.monitor_internal.use_name$ = '1' then
        |$endif
          |$if b.bit_overflow_internal.is_vector()
          |  $b.bit_overflow_internal.drive_name$($i$) := '1';
          |$else
          |  $b.bit_overflow_internal.drive_name$ := '1';
          |$endif
        |end if;
      |$endif
      |$state.d$@:= $state.d$@or $b.monitor_internal.use_name$;
    |$endif
    |$if b.cfg.monitor_mode == 'increment'
      |$if b.monitor_internal.is_vector()
        |if $b.monitor_internal.use_name$($i$) = '1' then
      |$else
        |if $b.monitor_internal.use_name$ = '1' then
      |$endif
      |  accum_add($state.a$, "1");
      |end if;
    |$endif
  |$endif
|$endblock

|$block READ
  |$if b.cfg.bus_read != 'disabled'
    |@ Read mode: $b.cfg.bus_read$.
    |$if b.underrun_internal is not None
      |@ If the field is already invalid, assert the underrun flag.
      |if $state.v$ = '0' then
        |$if b.underrun_internal.is_vector()
        |  $b.underrun_internal.drive_name$($i$) := '1';
        |$else
        |  $b.underrun_internal.drive_name$ := '1';
        |$endif
      |end if;
      |
      |@ Process the read action regardless of whether an underrun occurred.
    |$endif
  |$endif
  |$if b.cfg.bus_read == 'error'
    |r_nack@:= true;
  |$endif
  |$if b.cfg.bus_read in ['enabled', 'valid-wait', 'valid-only']
    |$r_data$@:= $state.d$;
    |$if b.cfg.bus_read in ['valid-wait', 'valid-only']
      |if $state.v$ = '1' then
      |  r_ack@:= true;
      |$ AFTER_READ
      |else
        |$if b.cfg.bus_read in ['valid-wait']
        |  r_block@:= true;
        |$else
        |  r_nack@:= true;
        |$endif
      |end if;
    |$else
      |r_ack@:= true;
      |$AFTER_READ
    |$endif
  |$endif
|$endblock

|$block AFTER_READ
  |$if b.cfg.after_bus_read != 'nothing'
    |@ Handle post-read operation: $b.cfg.after_bus_read$.
  |$endif
  |$if b.cfg.after_bus_read in ['invalidate', 'clear']
    |$if vec
      |$state.d$@:= (others => '0');
    |$else
      |$state.d$@:= '0';
    |$endif
  |$endif
  |$if b.cfg.after_bus_read == 'invalidate'
    |$state.v$@:= '0';
  |$endif
  |$if b.cfg.after_bus_read == 'increment'
    |accum_add($state.a$, "1");
  |$endif
  |$if b.cfg.after_bus_read == 'decrement'
    |accum_sub($state.a$, "1");
  |$endif
|$endblock

|$block WRITE
  |$if b.cfg.bus_write != 'disabled'
    |@ Write mode: $b.cfg.bus_write$.
    |$if b.cfg.ctrl_lock
      |if $lock[i]$ = '0' then
      |$ HANDLE_WRITE
      |end if;
    |$else
      |$HANDLE_WRITE
    |$endif
  |$endif
|$endblock

|$block HANDLE_WRITE
  |$if b.overrun_internal is not None
    |@ If the field is already valid, assert the overrun flag.
    |if $state.v$ = '1' then
      |$if b.overrun_internal.is_vector()
      |  $b.overrun_internal.drive_name$($i$) := '1';
      |$else
      |  $b.overrun_internal.drive_name$ := '1';
      |$endif
    |end if;
    |
    |@ Process the write action regardless of whether an overrun occurred.
  |$endif
  |$if b.cfg.bus_write == 'error'
    |w_nack@:= true;
  |$endif
  |$if b.cfg.bus_write == 'enabled'
    |$state.d$@:= $w_data$;
    |w_ack@:= true;
    |$AFTER_WRITE
  |$endif
  |$if b.cfg.bus_write.startswith('invalid')
    |if $state.v$ = '0' then
    |  $state.d$@:= $w_data$;
    |  w_ack@:= true;
    |$ AFTER_WRITE
    |else
      |$if b.cfg.bus_write == 'invalid'
      |  w_ack@:= true;
      |$endif
      |$if b.cfg.bus_write == 'invalid-wait'
      |  w_block@:= true;
      |$endif
      |$if b.cfg.bus_write == 'invalid-only'
      |  w_nack@:= true;
      |$endif
    |end if;
  |$endif
  |$if b.cfg.bus_write == 'masked'
    |$state.d$@:= ($state.d$ and not $w_strobe$)@or $w_data$;
    |w_ack@:= true;
    |$AFTER_WRITE
  |$endif
  |$if b.cfg.bus_write == 'accumulate'
    |accum_add($state.a$, $w_data$);
    |w_ack@:= true;
    |$AFTER_WRITE
  |$endif
  |$if b.cfg.bus_write == 'subtract'
    |accum_sub($state.a$, $w_data$);
    |w_ack@:= true;
    |$AFTER_WRITE
  |$endif
  |$if b.cfg.bus_write == 'bit-set'
    |$if b.bit_overflow_internal is not None
      |$if vec
        |if or_reduce($state.d$ and $w_data$) = '1' then
      |$else
        |if $state.d$ = '1' and $w_data$ = '1' then
      |$endif
        |$if b.bit_overflow_internal.is_vector()
        |  $b.bit_overflow_internal.drive_name$($i$) := '1';
        |$else
        |  $b.bit_overflow_internal.drive_name$ := '1';
        |$endif
      |end if;
    |$endif
    |$state.d$@:= $state.d$@or $w_data$;
    |w_ack@:= true;
    |$AFTER_WRITE
  |$endif
  |$if b.cfg.bus_write == 'bit-clear'
    |$if b.bit_underflow_internal is not None
      |$if vec
        |if or_reduce($w_data$ and not $state.d$) = '1' then
      |$else
        |if $state.d$ = '0' and $w_data$ = '1' then
      |$endif
        |$if b.bit_underflow_internal.is_vector()
        |  $b.bit_underflow_internal.drive_name$($i$) := '1';
        |$else
        |  $b.bit_underflow_internal.drive_name$ := '1';
        |$endif
      |end if;
    |$endif
    |$state.d$@:= $state.d$@and not $w_data$;
    |w_ack@:= true;
    |$AFTER_WRITE
  |$endif
  |$if b.cfg.bus_write == 'bit-toggle'
    |$state.d$@:= $state.d$@xor $w_data$;
    |w_ack@:= true;
    |$AFTER_WRITE
  |$endif
|$endblock

|$block AFTER_WRITE
  |$if b.cfg.after_bus_write != 'nothing'
    |@ Handle post-write operation: $b.cfg.after_bus_write$.
  |$endif
  |$if b.cfg.after_bus_write == 'validate'
    |$state.v$@:= '1';
  |$endif
  |$if b.cfg.after_bus_write == 'invalidate'
    |$state.v$@:= '1';
    |$state.inval$@:= '1';
  |$endif
|$endblock

|$block POST
  |$if accum
    |@ Handle accumulation for field $fd.name$.
    |accum_add($state.a$, $state.d$);
    |$if vec
      |$state.d$ := $state.a$($fd.base_bitrange.width-1$ downto 0);
    |$else
      |$state.d$ := $state.a$(0);
    |$endif
    |$if b.overflow_internal is not None or b.underflow_internal is not None
      |@ Handle over/underflow flags for field $fd.name$.
      |if $state.a$($fd.base_bitrange.width+1$ downto $fd.base_bitrange.width$) /= "00" then
        |$if b.overflow_internal is not None
        |  if $state.a$($fd.base_bitrange.width+2$) = '0' then
            |$if b.overflow_internal.is_vector()
          |    $b.overflow_internal.drive_name$($i$) := '1';
            |$else
          |    $b.overflow_internal.drive_name$ := '1';
            |$endif
        |  end if;
        |$endif
        |$if b.underflow_internal is not None
        |  if $state.a$($fd.base_bitrange.width+2$) = '1' then
            |$if b.underflow_internal.is_vector()
          |    $b.underflow_internal.drive_name$($i$) := '1';
            |$else
          |    $b.underflow_internal.drive_name$ := '1';
            |$endif
        |  end if;
        |$endif
      |end if;
    |$endif
  |$endif
  |$if b.cfg.hw_write != 'status'
    |@ Handle reset for field $fd.name$.
    |$if b.cfg.ctrl_reset
      |@ This includes the optional per-field reset control signal.
        |if reset = '1' or $reset[i]$ = '1' then
      |$else
        |if reset = '1' then
      |$endif
      |  $state.d$@:= $reset_data if isinstance(reset_data, str) else reset_data[i]$;
      |  $state.v$@:= $reset_valid$;
      |$if b.cfg.after_bus_write == 'invalidate'
        |  $state.inval$@:= '0';
      |$endif
    |end if;
  |$endif
  |$if b.cfg.hw_read in ('simple', 'enabled')
    |@ Assign the read outputs for field $fd.name$.
    |$data[i]$ <= $state.d$;
    |$if b.cfg.hw_read == 'enabled'
      |$valid[i]$ <= $state.v$;
    |$endif
  |$endif
  |$if b.cfg.hw_read == 'handshake'
    |@ Assign the ready output for field $fd.name$.
    |$ready[i]$ <= not $state.v$;
  |$endif
  |$if b.drive_internal is not None
    |@ Assign the internal signal for field $fd.name$.
    |$b.drive_internal.drive_name$ := $state.d$;
  |$endif
  |$if b.full_internal is not None
    |@ Assign the internal signal for the 'full' flag of field $fd.name$.
    |$if b.full_internal.is_vector()
      |$b.full_internal.drive_name$($i$) := $state.v$;
    |$else
      |$b.full_internal.drive_name$ := $state.v$;
    |$endif
  |$endif
  |$if b.empty_internal is not None
    |@ Assign the internal signal for the 'empty' flag of field $fd.name$.
    |$if b.empty_internal.is_vector()
      |$b.empty_internal.drive_name$($i$) := not $state.v$;
    |$else
      |$b.empty_internal.drive_name$ := not $state.v$;
    |$endif
  |$endif
|$endblock
