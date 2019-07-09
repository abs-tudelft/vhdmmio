"""Module for AXC passthrough fields."""

from .logic import FieldLogic
from .logic_registry import field_logic
from .accesscaps import AccessCapabilities, NoOpMethod
from ..template import TemplateEngine, annotate_block
from ..vhdl.types import Record, Array, Axi4Lite, gather_defs

_LOGIC_PRE = annotate_block("""
@ Complete the AXI stream handshakes that occurred in the previous cycle for
@ field $l.field_descriptor.meta.name$.
$if l.write_caps is not None
if $s2m[i]$.aw.ready = '1' then
  $state[i]$.aw.valid := '0';
end if;
if $s2m[i]$.w.ready = '1' then
  $state[i]$.w.valid := '0';
end if;
if $state[i]$.b.valid = '0' then
  $state[i]$.b := $s2m[i]$.b;
end if;
$endif
$if l.read_caps is not None
if $s2m[i]$.ar.ready = '1' then
  $state[i]$.ar.valid := '0';
end if;
if $state[i]$.r.valid = '0' then
  $state[i]$.r := $s2m[i]$.r;
end if;
$endif

$if l.interrupt is not None
@ Connect the incoming interrupt signal for field $l.field_descriptor.meta.name$
@ to the associated internal signal.
$if l.interrupt.width is None
$l.interrupt.drive_name$ := $s2m[i]$.u.irq;
$else
$l.interrupt.drive_name$($i$) := $s2m[i]$.u.irq;
$endif
$endif
""", comment='--')

_LOGIC_READ_REQUEST = annotate_block("""
if $state[i]$.ar.valid = '0' then
  $state[i]$.ar.addr := r_addr and $addr_mask$;
  $state[i]$.ar.prot := r_prot;
  $state[i]$.ar.valid := '1';
  r_defer := true;
elsif r_req then
  r_block := true;
end if;
""", comment='--')

_LOGIC_READ_RESPONSE = annotate_block("""
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
""", comment='--')

_LOGIC_WRITE_REQUEST = annotate_block("""
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
""", comment='--')

_LOGIC_WRITE_RESPONSE = annotate_block("""
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
""", comment='--')

_LOGIC_POST = annotate_block("""
@ Handle reset for field $l.field_descriptor.meta.name$.
if reset = '1' then
$if l.write_caps is not None
  $state[i]$.aw.valid := '0';
  $state[i]$.w.valid := '0';
  $state[i]$.b.valid := '0';
$endif
$if l.read_caps is not None
  $state[i]$.ar.valid := '0';
  $state[i]$.r.valid := '0';
$endif
end if;

@ Assign output ports for field $l.field_descriptor.meta.name$.
$if l.write_caps is not None
$m2s[i]$.aw <= $state[i]$.aw;
$m2s[i]$.w <= $state[i]$.w;
$m2s[i]$.b.ready <= not $state[i]$.b.valid;
$else
$m2s[i]$.aw <= AXI4LA_RESET;
$m2s[i]$.w <= AXI4LW$width$_RESET;
$m2s[i]$.b <= AXI4LH_RESET;
$endif
$if l.read_caps is not None
$m2s[i]$.ar <= $state[i]$.ar;
$m2s[i]$.r.ready <= not $state[i]$.r.valid;
$else
$m2s[i]$.ar <= AXI4LA_RESET;
$m2s[i]$.r <= AXI4LH_RESET;
$endif
""", comment='--')


@field_logic('axi')
class AXIField(FieldLogic):
    """AXI passthrough field."""

    def __init__(self, field_descriptor, dictionary):
        """Constructs an AXI passthrough field."""

        # Parse configuration options.
        read_support = bool(dictionary.pop('read_support', True))
        write_support = bool(dictionary.pop('write_support', True))
        interrupt_support = bool(dictionary.pop('interrupt_support', False))

        # Validate the field configuration.
        if field_descriptor.vector_width not in [32, 64]:
            raise ValueError('AXI field width must be 32 or 64 bits')
        if not read_support and not write_support:
            raise ValueError('cannot disable both read- and write support')

        # Register/connect internal interrupt signal.
        self._interrupt = None
        if interrupt_support:
            self._interrupt = self.field_descriptor.regfile.internal_signals.drive(
                self.field_descriptor,
                '%s_irq' % self.field_descriptor.meta.name,
                field_descriptor.vector_count)

        # Determine the read/write capability fields.
        if read_support:
            read_caps = AccessCapabilities(
                volatile=True, can_block=True, can_defer=True,
                no_op_method=NoOpMethod.NEVER, can_read_for_rmw=False)
        else:
            read_caps = None

        if write_support:
            write_caps = AccessCapabilities(
                volatile=True, can_block=True, can_defer=True,
                no_op_method=NoOpMethod.NEVER)
        else:
            write_caps = None

        super().__init__(
            field_descriptor=field_descriptor,
            read_caps=read_caps,
            write_caps=write_caps)

    def to_dict(self, dictionary):
        """Returns a dictionary representation of this object."""
        super().to_dict(dictionary)
        if self.read_caps is None:
            dictionary['read-support'] = False
        if self.write_caps is None:
            dictionary['write-support'] = False
        if self._interrupt is not None:
            dictionary['interrupt-support'] = True

    @property
    def interrupt(self):
        """The internal signal that is connected to the incoming interrupt
        request flag, or `None` if the interrupt flag is ignored."""
        return self._interrupt

    def generate_vhdl(self, gen):
        """Generates the VHDL code for the associated field by updating the
        given `vhdl.Generator` object."""

        tple = TemplateEngine()
        tple['l'] = self
        tple['width'] = self.vector_width
        mask = (1 << self.field_descriptor.fields[0].bitrange.size) - 1
        tple['addr_mask'] = 'X"%08X"' % mask

        # Generate interface.
        tple['m2s'] = gen.add_field_port(
            self.field_descriptor, 'o', 'o', Axi4Lite('m2s', self.vector_width))
        tple['s2m'] = gen.add_field_port(
            self.field_descriptor, 'i', 'i', Axi4Lite('s2m', self.vector_width))

        # Generate internal state.
        state_name = 'f_%s_r' % self.field_descriptor.meta.name
        state_record = Record(state_name)
        components = []
        if self.write_caps is not None:
            components.extend(['aw', 'w', 'b'])
        if self.read_caps is not None:
            components.extend(['ar', 'r'])
        for component in components:
            state_record.append(component, Axi4Lite(component, self.vector_width))
        state_array = Array(state_name, state_record)
        count = 1
        if self.vector_count is not None:
            count = self.vector_count
        state_decl, state_ob = state_array.make_variable(state_name, count)
        tple['state'] = state_ob
        state_defs = gather_defs(state_array)
        state_defs.append(state_decl + ';')
        gen.add_field_declarations(self.field_descriptor, private='\n'.join(state_defs))

        # Ignore some variables when expanding this template; they will be
        # expanded by the add_field_*_logic() functions.
        tple.passthrough('i', 'r_data', 'w_data', 'w_strobe')

        def expand(template):
            expanded = tple.apply_str_to_str(template, postprocess=False)
            if not expanded.strip():
                expanded = None
            return expanded

        gen.add_field_interface_logic(
            self.field_descriptor,
            expand(_LOGIC_PRE),
            expand(_LOGIC_POST))

        if self.read_caps is not None:
            gen.add_field_read_logic(
                self.field_descriptor,
                both=expand(_LOGIC_READ_REQUEST),
                deferred=expand(_LOGIC_READ_RESPONSE))

        if self.write_caps is not None:
            gen.add_field_write_logic(
                self.field_descriptor,
                both=expand(_LOGIC_WRITE_REQUEST),
                deferred=expand(_LOGIC_WRITE_RESPONSE))
