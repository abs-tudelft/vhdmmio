if $state[i]$.aw.valid = '0' and $state[i]$.w.valid = '0' then
$if l.offset is None
  $state[i]$.aw.addr := w_addr;
$else
$if isinstance(l.offset, int)
  $state[i]$.aw.addr := X"$('{:0%dX}' % width).format(l.offset)$";
$else
  $state[i]$.aw.addr := (others => '0');
  $state[i]$.aw.addr($block_size+l.offset.width-1$ downto $block_size$) := $l.offset.use_name$;
$endif
  $state[i]$.aw.addr($block_size-1$ downto $bus_size$) := w_addr($block_size-1$ downto $bus_size$);
$endif
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
