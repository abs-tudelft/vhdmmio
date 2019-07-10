if $state[i]$.ar.valid = '0' then
$if l.offset is None
  $state[i]$.ar.addr := r_addr;
$else
$if isinstance(l.offset, int)
  $state[i]$.ar.addr := X"$('{:0%dX}' % width).format(l.offset)$";
$else
  $state[i]$.ar.addr := (others => '0');
  $state[i]$.ar.addr($block_size+l.offset.width-1$ downto $block_size$) := $l.offset.use_name$;
$endif
  $state[i]$.ar.addr($block_size-1$ downto $bus_size$) := r_addr($block_size-1$ downto $bus_size$);
$endif
  $state[i]$.ar.prot := r_prot;
  $state[i]$.ar.valid := '1';
  r_defer := true;
elsif r_req then
  r_block := true;
end if;
