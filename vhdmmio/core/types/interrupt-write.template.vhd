@ Write mode: $l.write$.
$if l.write == 'enabled'
$v$ := ($v$ and not $w_strobe$) or $w_data$;
$endif
$if l.write == 'clear'
$v$ := $v$ and not $w_data$;
$endif
$if l.write == 'set'
$v$ := $v$ or $w_data$;
$endif
w_ack := true;
