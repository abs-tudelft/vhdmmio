@ Write mode: $cfg.bus_write$.
$if cfg.bus_write == 'enabled'
$v$ := ($v$ and not $w_strobe$) or $w_data$;
$endif
$if cfg.bus_write == 'clear'
$v$ := $v$ and not $w_data$;
$endif
$if cfg.bus_write == 'set'
$v$ := $v$ or $w_data$;
$endif
w_ack := true;
