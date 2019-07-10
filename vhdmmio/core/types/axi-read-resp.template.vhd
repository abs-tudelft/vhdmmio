if $state[i]$.r.valid = '1' then
  $r_data$ := $state[i]$.r.data;
  case $state[i]$.r.resp is
    when AXI4L_RESP_OKAY => r_ack := true;
    when AXI4L_RESP_DECERR => null;
    when others => r_nack := true;
  end case;
  $state[i]$.r.valid := '0';
else
  r_block := true;
end if;
