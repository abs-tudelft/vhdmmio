if $state[i]$.aw.valid = '0' and $state[i]$.w.valid = '0' then
  $state[i]$.aw.addr := w_addr and $addr_mask$;
  $state[i]$.aw.prot := w_prot;
  $state[i]$.aw.valid := '1';

  @ The magic below assigns the strobe signals properly in the way that the
  @ field logic templates are supposed to. It doesn't make much sense unless
  @ you know that w_strobe in the template maps to $w_strobe$, including
  @ the slice, and you know that VHDL doesn't allow indexation of slices. So
  @ we need a temporary storage location of the right size; data qualifies.
  $state[i]$.w.data := $w_strobe$;
  for i in 0 to $width//8-1$ loop
    $state[i]$.w.strb(i) := $state[i]$.w.data(i*8);
  end loop;

  @ Now set the actual data, of course.
  $state[i]$.w.data := $w_data$;
  $state[i]$.w.valid := '1';

  w_defer := true;
elsif w_req then
  w_block := true;
end if;
