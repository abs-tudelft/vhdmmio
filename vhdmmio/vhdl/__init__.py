"""Module for generating VHDL code for register files."""

import os
from collections import OrderedDict
from enum import Enum
from ..template import TemplateEngine, annotate_block
from .decoder import Decoder
from .types import Record, Array, SizedArray, Axi4Lite, Object, gather_defs
from .interface import Interface

_BUS_REQ_FIELD_TEMPLATE = annotate_block("""
$block HANDLE
$if defined('LOOKAHEAD')
if $dir$_lreq then
$ LOOKAHEAD
end if;
$endif
$if defined('NORMAL')
if $dir$_req then
$ NORMAL
end if;
$endif
$if defined('BOTH')
if $dir$_req or $dir$_lreq then
$ BOTH
end if;
$endif
$endblock

@ ${'r': 'Read', 'w': 'Write'}[dir]$ logic for $desc$
$if prot == '---'
$HANDLE
$else
if std_match($dir$_prot, "$prot$") then
$ HANDLE
end if;
$endif
""", comment='--')

_BUS_REQ_BOILERPLATE_TEMPLATE = annotate_block("""
$block BEFORE_READ
@ Clear holding register location prior to read.
r_hold($bw*blk + bw-1$ downto $bw*blk$) := (others => '0');
$endblock

$block AFTER_READ
$if cur_cnt > 1
@ Read logic for block $blk$ of $desc$
$else
@ Read logic for $desc$
$endif
if r_req then
  r_data := r_hold($bw*blk + bw-1$ downto $bw*blk$);
$if cur_cnt > 1
$if blk == 0
  r_multi := '1';
$else
  if r_multi = '1' then
    r_ack := true;
  else
    r_nack := true;
  end if;
$endif
$endif
$if blk == cur_cnt - 1
  r_multi := '0';
$endif
end if;
$if blk == 0 and read_tag is not None
if r_defer then
  r_dtag := $read_tag$;
end if;
$endif
$endblock

$block BEFORE_WRITE
$if cur_cnt > 1
@ Write logic for block $blk$ of $desc$
$else
@ Write logic for $desc$
$endif
if w_req then
  w_hold($bw*blk + bw-1$ downto $bw*blk$) := w_data;
  w_hstb($bw*blk + bw-1$ downto $bw*blk$) := w_strb;
  w_multi := '$'1' if blk < cur_cnt - 1 else '0'$';
end if;
$endblock

$block AFTER_WRITE
$if blk == cur_cnt - 1 and write_tag is not None
if w_defer then
  w_dtag := $write_tag$;
end if;
$endif
$endblock

$if dir == 'r'
$if pos == 'before'
$BEFORE_READ
$else
$AFTER_READ
$endif
$else
$if pos == 'before'
$BEFORE_WRITE
$else
$AFTER_WRITE
$endif
$endif
""", comment='--')

_INTERNAL_SIGNAL_BOILERPLATE_TEMPLATE = annotate_block("""
$if s.is_strobe
$s.use_name$ := $s.drive_name$;
$s.drive_name$ := $c$;
$endif
if reset = '1' then
  $s.use_name$ := $c$;
end if;
""", comment='--')

class Generator:
    """VHDL generator for register files."""

    def __init__(self, regfile):
        """Constructs a VHDL generator for the given register file."""
        super().__init__()
        self._regfile = regfile

        # Main template engine, used to generate the actual VHDL files.
        self._tple = TemplateEngine()
        self._tple['r'] = regfile

        # Interface builder.
        self._interface = Interface(regfile.meta.name)

        # Address decoder builders.
        self._read_decoder = Decoder('r_addr', 32, optimize=regfile.optimize)
        self._read_tag_decoder = Decoder('r_rtag', regfile.read_tag_width, optimize=True)
        self._write_decoder = Decoder('w_addr', 32, optimize=regfile.optimize)
        self._write_tag_decoder = Decoder('w_rtag', regfile.write_tag_width, optimize=True)

        # Generate code for interrupts.
        for interrupt in regfile.interrupts:
            interrupt.generate_vhdl(self)

        # Generate boilerplate register access code before field code.
        for register in regfile.registers:
            self._add_register_boilerplate(register, 'before')

        # Generate code for fields.
        for field_descriptor in regfile.field_descriptors:
            field_descriptor.logic.generate_vhdl(self)

        # Generate boilerplate register access code after field code.
        for register in regfile.registers:
            self._add_register_boilerplate(register, 'after')

        # Add the decoders to the main template engine.
        self._read_decoder.append_to_template(
            self._tple, 'FIELD_LOGIC_READ',
            'Read address decoder.')
        self._read_tag_decoder.append_to_template(
            self._tple, 'FIELD_LOGIC_READ_TAG',
            'Deferred read tag decoder.')
        self._write_decoder.append_to_template(
            self._tple, 'FIELD_LOGIC_WRITE',
            'Write address decoder.')
        self._write_tag_decoder.append_to_template(
            self._tple, 'FIELD_LOGIC_WRITE_TAG',
            'Deferred write tag decoder.')

        # Add the interface to the main template engine.
        for block in self._interface.generate('port'):
            self._tple.append_block('PORTS', block)
        for block in self._interface.generate('generic', end_with_semicolon=False):
            self._tple.append_block('GENERICS', block)
        typedefs = gather_defs(*self._interface.gather_types())
        if typedefs:
            self._tple.append_block(
                'PACKAGE',
                '@ Types used by the register file interface.',
                '\n'.join(typedefs))

        # Generate code for internal signals.
        for internal_signal in regfile.internal_signals:
            self._add_internal_signal_boilerplate(internal_signal)

    def generate_files(self, output_directory, annotate=False):
        """Generates the files for this register file in the specified
        directory."""
        relpath = ''
        if self._regfile.output_directory is not None:
            relpath = os.path.relpath(self._regfile.output_directory)
        output_directory = output_directory.replace('@', relpath)
        if not os.path.exists(output_directory):
            os.makedirs(output_directory)
        name = output_directory + os.sep + self._regfile.meta.name

        self._tple.apply_file_to_file(
            os.path.dirname(__file__) + os.sep + 'entity.template.vhd',
            name + '.gen.vhd',
            comment='-- ', annotate=annotate)
        print('Wrote %s.vhd' % name)

        self._tple.apply_file_to_file(
            os.path.dirname(__file__) + os.sep + 'package.template.vhd',
            name + '_pkg.gen.vhd',
            comment='-- ', annotate=annotate)
        print('Wrote %s_pkg.vhd' % name)

    def gather_ports(self):
        """Yields all the inputs/outputs/generics excluding `clk` and `reset`
        as `(mode, path, type, count)` four-tuples. `mode` is `'i'` for
        inputs, `'o'` for outputs, and `'g'` for generics. `count` is `None` if
        the type is not an incomplete array."""
        for mode, name, typ, count in self._interface.gather_ports():
            yield mode, name, typ, count
        yield 'i', 'bus_i', Axi4Lite('m2s', self._regfile.bus_width), None
        yield 'o', 'bus_o', Axi4Lite('s2m', self._regfile.bus_width), None

    @staticmethod
    def _describe_interrupt(interrupt):
        """Generates a description for an interrupt, to be used as block
        comment."""
        return '%s-sensitive interrupt %s: %s' % (
            'strobe' if interrupt.can_clear else 'level',
            interrupt.meta[None].markdown_name,
            interrupt.meta[None].markdown_brief)

    @staticmethod
    def _describe_field_descriptor(field_descriptor):
        """Generates a description for a field descriptor, to be used as block
        comment."""
        return 'field %s%s: %s' % (
            'group ' if field_descriptor.vector_count is not None else '',
            field_descriptor.meta[None].markdown_name,
            field_descriptor.meta[None].markdown_brief)

    @staticmethod
    def _describe_field(field):
        """Generates a description for a field, to be used as block comment."""
        return 'field %s: %s' % (
            field.meta.markdown_name,
            field.meta.markdown_brief)

    @staticmethod
    def _describe_register(register):
        """Generates a description for a register, to be used as block
        comment."""
        return 'register %s: %s' % (
            register.meta.markdown_name,
            register.meta.markdown_brief)

    def add_interrupt_port(self, interrupt, name, mode, typ, count=None):
        """Registers a port for the given interrupt with the specified
        (namespaced) name, mode (`'i'` for inputs or `'o'` for outputs), type
        object from `.types`, and if the latter is an incomplete array, its
        size. Returns an object that represents the interface, which must be
        indexed by the interrupt index first (index is ignored if the interrupt
        is scalar) to get the requested type. It can then be converted to a
        string to get the VHDL representation."""
        return self._interface.add(
            interrupt.meta.name, self._describe_interrupt(interrupt), 'i', None,
            name, mode, typ, count,
            interrupt.iface_opts)

    def add_interrupt_generic(self, interrupt, name, typ, count=None):
        """Registers a generic for the given interrupt with the specified
        (namespaced) name, type object from `.types`, and if the latter is
        an incomplete array, its size. Returns an object that represents the
        interface, which must be indexed by the interrupt index first (index is
        ignored if the interrupt is scalar) to get the requested type. It can
        then be converted to a string to get the VHDL representation."""
        return self._interface.add(
            interrupt.meta.name, self._describe_interrupt(interrupt), 'i', None,
            name, 'g', typ, count,
            interrupt.iface_opts)

    def add_field_port(self, field_descriptor, name, mode, typ, count=None):
        """Registers a port for the given field with the specified
        (namespaced) name, mode (`'i'` for inputs or `'o'` for outputs), type
        object from `.types`, and if the latter is an incomplete array, its
        size. Returns an object that represents the interface, which must be
        indexed by the field index first (index is ignored if the field
        is scalar) to get the requested type. It can then be converted to a
        string to get the VHDL representation."""
        return self._interface.add(
            field_descriptor.meta.name,
            self._describe_field_descriptor(field_descriptor),
            'f', field_descriptor.vector_count,
            name, mode, typ, count,
            field_descriptor.iface_opts)

    def add_field_generic(self, field_descriptor, name, typ, count=None):
        """Registers a generic for the given field with the specified
        (namespaced) name, type object from `.types`, and if the latter is
        an incomplete array, its size. Returns an object that represents the
        interface, which must be indexed by the field index first (index is
        ignored if the field is scalar) to get the requested type. It can
        then be converted to a string to get the VHDL representation."""
        return self._interface.add(
            field_descriptor.meta.name,
            self._describe_field_descriptor(field_descriptor),
            'f', field_descriptor.vector_count,
            name, 'g', typ, count,
            field_descriptor.iface_opts)

    def _add_block(self, key, region, desc, block):
        if block is not None:
            self._tple.append_block(key, '@ %s for %s' % (region, desc), block)

    def _add_declarations(self, desc, private, public, body):
        """Registers declarative code blocks, expanded into respectively the
        process header, package header, and package body. `desc` is used for
        generating the comment that is placed above the blocks."""
        self._add_block('DECLARATIONS', 'Private declarations', desc, private)
        self._add_block('PACKAGE', 'Public declarations', desc, public)
        self._add_block('PACKAGE_BODY', 'Implementations', desc, body)

    def add_interrupt_declarations(self, interrupt, private=None, public=None, body=None):
        """Registers declarative code blocks for the given interrupt,
        expanded into respectively the process header, package header, and
        package body. A comment identifying the interrupt is added before the
        blocks automatically."""
        self._add_declarations(
            self._describe_interrupt(interrupt),
            private, public, body)

    def add_field_declarations(self, field_descriptor, private=None, public=None, body=None):
        """Registers declarative code blocks for the given field descriptor,
        expanded into respectively the process header, package header, and
        package body. A comment identifying the field is added before the blocks
        automatically."""
        self._add_declarations(
            self._describe_field_descriptor(field_descriptor),
            private, public, body)

    def add_interrupt_logic(self, interrupt, logic):
        """Registers the code block for the logic of the specified interrupt.
        The generated block is executed every cycle. The block must indicate
        whether the interrupt(s) is/are asserted by writing to the `i_req`
        variable. This is an `std_logic_vector` shared between all interrupts;
        it must be indexed using `interrupt.low` and `interrupt.high`. It is
        active-high."""
        self._add_block(
            'IRQ_LOGIC', 'Interrupt logic',
            self._describe_interrupt(interrupt), logic)

    def add_field_interface_logic(self, field_descriptor, pre=None, post=None):
        """Registers code templates for the hardware interface of the specified
        field. `pre` is placed before the bus interface logic, `post` is placed
        after. These blocks are executed every cycle for each (enabled) field
        in the descriptor. The template parameter `$i$` can be used for the
        field index. A comment identifying the field is added before the blocks
        automatically."""
        tple = TemplateEngine()
        tple['desc'] = self._describe_field_descriptor(field_descriptor)
        template = '@ $position$-bus logic for $desc$\n'
        if field_descriptor.vector_count is None:
            template += '$BLOCK'
            tple['i'] = '0'
        else:
            template += 'for i in 0 to $count-1$ loop\n$ BLOCK\nend loop;'
            tple['count'] = field_descriptor.vector_count
            tple['i'] = 'i'
        if pre is not None:
            tple['position'] = 'Pre'
            tple.append_block('BLOCK', pre)
            block = tple.apply_str_to_str(template, postprocess=False)
            self._tple.append_block('FIELD_LOGIC_BEFORE', block)
        if post is not None:
            tple['position'] = 'Post'
            tple.reset_block('BLOCK')
            tple.append_block('BLOCK', post)
            block = tple.apply_str_to_str(template, postprocess=False)
            self._tple.append_block('FIELD_LOGIC_AFTER', block)

    def _add_field_bus_logic(self, field_descriptor, direction, normal, lookahead, both, deferred):
        """Implements `add_field_read_logic()` and `add_field_write_logic()`.
        They are distinguished through `direction`, which must be `'r'` or
        `'w'`."""
        for index, field in enumerate(field_descriptor.fields):

            # Determine the address that the regular field logic should be
            # activated for.
            register = field.register
            address = register.address
            if direction == 'w':
                address += (1 << register.block_size) * (register.block_count - 1)
            mask = (1 << register.block_size) - 1

            # Describe the field for use in comments.
            desc = self._describe_field(field)

            # Create a template engine for processing the incoming blocks.
            tple = TemplateEngine()
            tple['i'] = index
            if field.bitrange.is_vector():
                rnge = '%d downto %d' % (field.bitrange.high_bit, field.bitrange.low_bit)
            else:
                rnge = '%d' % field.bitrange.low_bit
            tple['r_data'] = 'r_hold(%s)' % rnge
            tple['w_data'] = 'w_hold(%s)' % rnge
            tple['w_strobe'] = 'w_hstb(%s)' % rnge
            tple['desc'] = desc
            tple['dir'] = direction
            if direction == 'r':
                tple['prot'] = field_descriptor.read_prot
            else:
                tple['prot'] = field_descriptor.write_prot

            # Add the normal and lookahead blocks.
            if normal is not None:
                tple.append_block('NORMAL', '@ Regular access logic.', normal)
            if lookahead is not None:
                tple.append_block('LOOKAHEAD', '@ Lookahead logic.', lookahead)
            if both is not None:
                tple.append_block('BOTH', '@ Access logic.', both)
            block = tple.apply_str_to_str(_BUS_REQ_FIELD_TEMPLATE, postprocess=False)
            decoder = {'r': self._read_decoder, 'w': self._write_decoder}[direction]
            decoder.add_action(block, address, mask)

            # Add the deferred block.
            if deferred is not None:
                tag = {'r': register.read_tag, 'w': register.write_tag}[direction]
                assert tag is not None and tag.startswith('"') and tag.endswith('"')
                tag = int(tag[1:-1], 2)
                decoder = {'r': self._read_tag_decoder, 'w': self._write_tag_decoder}[direction]
                decoder.add_action(
                    '@ Deferred %s logic for %s\n%s' % (
                        {'r': 'read', 'w': 'write'}[direction],
                        desc, tple.apply_str_to_str(deferred, postprocess=False)),
                    tag)

    def add_field_read_logic(
            self, field_descriptor,
            normal=None, lookahead=None, both=None, deferred=None):
        """Registers code blocks for handling bus reads for the given field.
        The blocks can make use of the template variable `$i$` for getting the
        index of the field that is being expanded. The generator ensures that
        the generated code is only executed when the field is addressed,
        enabled, and the bus logic is performing the following actions:

         - `normal`: the bus is currently accessing the field, and the bus
           response buffers are ready to accept the read result. `r_prot` holds
           the protection flags for the read. The block can do the following
           things to interact with the bus:

            - Set `r_ack` to `true` and `$r_data$` to the read result.
            - Set `r_nack` to `true` to respond with a slave error.
            - Set `r_block` to `true` to stall, IF the `can_block` flag was
              set for the field's read capabilities. In this case, the block
              will be executed again the next cycle.
            - Set `r_defer` to `true` to defer, IF the `can_defer` flag was
              set for the field's read capabilities. In this case, the request
              logic will accept the bus request and send subsequent requests
              to `lookahead` blocks, while the response logic will start
              calling the `deferred` block to get the response.
            - Nothing: the bus behaves as if the field does not exist. If there
              are no other fields in the addressed register, a decode error is
              returned.

         - `lookahead`: the bus is currently accessing the field, but the
           response logic is not ready for the result yet. This can happen
           because the response channels are still blocked or because this or
           another field deferred a previous request. It can be useful for
           fields that have a long access time. `r_prot` holds the protection
           flags for the read. The block can do the following things to
           interact with the bus:

            - Set `r_defer` to `true` to defer, IF the `can_defer` flag was
              set for the field's read capabilities. In this case, the request
              logic will accept the bus request and send subsequent requests
              to `lookahead` blocks, while the response logic will start
              calling the `deferred` block to get the response when the
              response logic does become ready.
            - Nothing: the bus logic will continue calling the lookahead block
              until the response logic is ready for the response, at which
              point it will call the `normal` block.

         - `deferred`: the `normal` or `lookahead` deferred a read in a
           preceding cycle, and the response logic is ready to accept the read
           result. Multiple accesses can be deferred this way by the same
           field; in all cases it is up to the field to memorize the associated
           protection flags if it needs them. The block can do the following
           things to interact with the bus:

            - Set `r_ack` to `true` and `$r_data$` to the read result to
              complete the transfer.
            - Set `r_nack` to `true` to respond with a slave error.
            - Set `r_block` to `true` to stall, IF the `can_block` flag was
              set for the field's read capabilities. In this case, the block
              will be executed again the next cycle.
            - Nothing: the bus behaves as if the field does not exist. If there
              are no other fields in the addressed register, a decode error is
              returned.
        """
        self._add_field_bus_logic(field_descriptor, 'r', normal, lookahead, both, deferred)

    def add_field_write_logic(
            self, field_descriptor,
            normal=None, lookahead=None, both=None, deferred=None):
        """Registers code blocks for handling bus writes for the given
        field. The blocks can make use of the template variable `$i$` for
        getting the index of the field that is being expanded. The generator
        ensures that the generated code is only executed when the register
        that the field belongs to is addressed, enabled, and the bus logic is
        performing the following actions:

         - `normal`: the bus is currently writing to the register that the
           field belongs to, and the bus response buffers are ready to accept
           the write result. `$w_data$` and `$w_strobe$` hold the data that is
           being written. Both variables are `std_logic` or an appropriately
           sized `std_logic_vector` for the field. They carry the following
           significance:

            - `$w_strobe$` low, `$w_data$` low: bit was not written/was masked
              out.
            - `$w_strobe$` high, `$w_data$` low: bit was written zero.
            - `$w_strobe$` high, `$w_data$` high: bit was written one.

           `$w_strobe$` and `$w_data$` high is illegal; one can assume that the
           data for a masked bit is always zero. Note that it is possible that
           none of the bits belonging to the field were actually written; if
           the field wishes to honor the strobe bits, it must do so manually.
           `w_prot` furthermore holds the protection flags for the write. The
           block can do the following things to interact with the bus:

            - Set `w_ack` to `true` to acknowledge the request.
            - Set `w_nack` to `true` to respond with a slave error.
            - Set `w_block` to `true` to stall, IF the `can_block` flag was
              set for the field's write capabilities. In this case, the block
              will be executed again the next cycle.
            - Set `w_defer` to `true` to defer, IF the `can_defer` flag was
              set for the field's write capabilities. In this case, the request
              logic will accept the bus request and send subsequent requests
              to `lookahead` blocks, while the response logic will start
              calling the `deferred` block to get the response.
            - Nothing: the bus behaves as if the field does not exist. If there
              are no other fields in the addressed register, a decode error is
              returned.

         - `lookahead`: the bus is currently accessing the field, but the
           response logic is not ready for the result yet. This can happen
           because the response channels are still blocked or because this or
           another field deferred a previous request. It can be useful for
           fields that have a long access time. `$w_data$`, `$w_strobe$`, and
           `w_prot` carry the same significance that they do for the `normal`
           block. The block can do the following things to interact with the
           bus:

            - Set `w_defer` to `true` to defer, IF the `can_defer` flag was
              set for the field's write capabilities. In this case, the request
              logic will accept the bus request and send subsequent requests
              to `lookahead` blocks, while the response logic will start
              calling the `deferred` block to get the response when the
              response logic does become ready.
            - Nothing: the bus logic will continue calling the lookahead block
              until the response logic is ready for the response, at which
              point it will call the `normal` block.

         - `deferred`: the `normal` or `lookahead` deferred a write in a
           preceding cycle, and the response logic is ready to accept the read
           result. Multiple accesses can be deferred this way by the same
           field; in all cases it is up to the field to memorize the associated
           write data and protection flags if it still needs them. The block
           can do the following things to interact with the bus:

            - Set `w_ack` to `true` to complete the transfer.
            - Set `w_nack` to `true` to respond with a slave error.
            - Set `w_block` to `true` to stall, IF the `can_block` flag was
              set for the field's write capabilities. In this case, the block
              will be executed again the next cycle.
            - Nothing: the bus behaves as if the field does not exist. If there
              are no other fields in the addressed register, a decode error is
              returned.
        """
        self._add_field_bus_logic(field_descriptor, 'w', normal, lookahead, both, deferred)

    def _add_register_boilerplate(self, register, position):
        """Adds the boilerplate bus logic for the given register. `position`
        indicates the relation of this function call with respect to the
        functions that add the field logic; if `'before'`, the function assumes
        that it is called before the field logic is added, if `'after'` it
        assumes after. Both variants must be called exactly once for each
        register."""
        mask = (1 << register.block_size) - 1
        tple = TemplateEngine()
        tple['pos'] = position
        tple['bw'] = register.regfile.bus_width
        tple['desc'] = self._describe_register(register)
        tple['cur_cnt'] = register.block_count
        tple['read_tag'] = register.read_tag
        tple['write_tag'] = register.write_tag
        for block_index in range(register.block_count):
            tple['blk'] = block_index
            address = register.address + (1 << register.block_size) * block_index
            if register.read_caps is not None:
                tple['dir'] = 'r'
                block = tple.apply_str_to_str(
                    _BUS_REQ_BOILERPLATE_TEMPLATE, postprocess=False)
                self._read_decoder.add_action(block, address, mask)
            if register.write_caps is not None:
                tple['dir'] = 'w'
                block = tple.apply_str_to_str(
                    _BUS_REQ_BOILERPLATE_TEMPLATE, postprocess=False)
                self._write_decoder.add_action(block, address, mask)

    def _add_internal_signal_boilerplate(self, internal_signal):
        """Adds the boilerplate logic for the given internal signal."""
        desc = 'internal signal %s' % internal_signal.name

        # Determine signal type name and reset value.
        if internal_signal.width is None:
            clear = "'0'"
            typ = 'std_logic'
        else:
            clear = "(others => '0')"
            typ = 'std_logic_vector(%d downto 0)' % (internal_signal.width - 1)

        # Variable declarations.
        block = 'variable %s : %s := %s;' % (internal_signal.use_name, typ, clear)
        if internal_signal.drive_name != internal_signal.use_name:
            block += '\nvariable %s : %s := %s;' % (internal_signal.drive_name, typ, clear)
        self._add_declarations(desc, block, None, None)

        # Boilerplate logic.
        tple = TemplateEngine()
        tple['s'] = internal_signal
        tple['c'] = clear
        block = tple.apply_str_to_str(
            _INTERNAL_SIGNAL_BOILERPLATE_TEMPLATE, postprocess=False)
        self._add_block('INTERNAL_SIGNAL_LOGIC', 'Logic', desc, block)

def generate(regfiles, output_directory, annotate=False):
    """Generates the VHDL files for the given list of register files.

    The files are written to `output_directory`. If you add an `@` symbol into
    the path, it will be replaced with the relative path from the working
    directory to the description file associated with the register file (or
    with an empty string if the filename is not known). Directories are
    automatically created if they don't exist yet.

    If `annotate` is set, the output files include comments that mark the
    template origin of most lines of code. This can be useful when debugging
    `vhdmmio` itself."""
    for regfile in regfiles:
        Generator(regfile).generate_files(output_directory, annotate=annotate)

def generate_pkg(output_directory):
    """Writes the `vhdmiio_pkg.gen.vhd` file to the given directory. If the
    directory does not exist yet, it is automatically created."""
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
    fname = output_directory + os.sep + 'vhdmmio_pkg.gen.vhd'

    with open(os.path.dirname(__file__) + os.sep + 'vhdmmio_pkg.vhd', 'r') as fil:
        data = fil.read()
    with open(fname, 'w') as fil:
        fil.write(data)
    print('Wrote %s.vhd' % fname)
