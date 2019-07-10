if $state[i]$.b.valid = '1' then
  case $state[i]$.b.resp is
    when AXI4L_RESP_OKAY => w_ack := true;
    when AXI4L_RESP_DECERR => null;
    when others => w_nack := true;
  end case;
  $state[i]$.b.valid := '0';
else
  w_block := true;
end if;
