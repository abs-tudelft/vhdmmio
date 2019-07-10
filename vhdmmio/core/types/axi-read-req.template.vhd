if $state[i]$.ar.valid = '0' then
  $state[i]$.ar.addr := r_addr and $addr_mask$;
  $state[i]$.ar.prot := r_prot;
  $state[i]$.ar.valid := '1';
  r_defer := true;
elsif r_req then
  r_block := true;
end if;
