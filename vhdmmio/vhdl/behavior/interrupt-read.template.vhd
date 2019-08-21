@ Read mode: $cfg.bus_read$.
$r_data$ := $v$;
$if cfg.bus_read == 'clear'
$v$ := '0';
$endif
r_ack := true;
