|@ Read mode: read $'and clear %s' % cfg.mode if cfg.bus_read == 'clear' else cfg.mode$.
|$r_data$ := $v$;
|$if cfg.bus_read == 'clear'
  |$v$ := '0';
|$endif
|r_ack := true;
