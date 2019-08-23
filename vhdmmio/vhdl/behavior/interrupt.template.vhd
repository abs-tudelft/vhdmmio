|$block READ
  |@ Read mode: read $'and clear %s' % cfg.mode if cfg.bus_read == 'clear' else cfg.mode$.
  |$r_data$ := $v$;
  |$if cfg.bus_read == 'clear'
    |$v$ := '0';
  |$endif
  |r_ack := true;
|$endblock

|$block WRITE
  |$if cfg.bus_write == 'enabled'
    |@ Write mode: set $cfg.mode$.
    |$v$ := ($v$ and not $w_strobe$) or $w_data$;
  |$endif
  |$if cfg.bus_write == 'clear'
    |@ Write mode: bit-clear $cfg.mode$.
    |$v$ := $v$ and not $w_data$;
  |$endif
  |$if cfg.bus_write == 'set'
    |@ Write mode: bit-set $cfg.mode$.
    |$v$ := $v$ or $w_data$;
  |$endif
  |w_ack := true;
|$endblock
