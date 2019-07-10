@ Read mode: $l.read$.
$r_data$ := $v$;
$if l.read == 'clear'
$v$ := '0';
$endif
r_ack := true;
