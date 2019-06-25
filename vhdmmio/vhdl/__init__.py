"""Module for generating VHDL code for register files."""

import os
from collections import OrderedDict
from ..template import TemplateEngine
from .match import match_template
from .types import Array

_BUS_REQ_FIELD_TEMPLATE = """
@ ${'r': 'Read', 'w': 'Write'}[dir]$ logic for $desc$
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
"""

_BUS_REQ_BOILERPLATE_TEMPLATE = """
$block BEFORE_READ
$if cnt > 1
@ Read logic for block $blk$ of $desc$
$else
@ Read logic for $desc$
$endif
$endblock

$block AFTER_READ
if r_req then
  r_data := r_hold($bw*blk + bw-1$ downto $bw*blk$);
$if cnt > 1
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
$if blk == cnt - 1
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
$if cnt > 1
@ Write logic for block $blk$ of $desc$
$else
@ Write logic for $desc$
$endif
if w_req then
  w_hold($bw*blk + bw-1$ downto $bw*blk$) := w_data;
  w_hstb($bw*blk + bw-1$ downto $bw*blk$) := w_strb;
  w_multi := '$'1' if blk < cnt - 1 else '0'$';
end if;
$endblock

$block AFTER_WRITE
$if blk == cnt - 1 and write_tag is not None
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
"""

class _Decoder:
    """Builder class for address decoders."""

    def __init__(self, address, num_bits, optimize=False):
        """Constructs an address decoder builder. The address decoder will
        match the address signal or variable named by `address`, which must be
        an `std_logic_vector(num_bits - 1 downto 0)`. If `optimize` is set,
        the action for any address for which no action is specified is
        interpreted as don't care, versus the default no-operation behavior."""
        super().__init__()
        self._num_bits = num_bits
        self._optimize = optimize
        self._tple = TemplateEngine()
        self._tple['address'] = address
        self._addresses = set()

    def add_action(self, block, address, mask=0):
        """Registers the given code block for execution when the address
        input matches `address`, with any high bits in `mask` masked *out*."""
        self._addresses.add((address, mask))
        self._tple.append_block('ADDR_0x%x' % address, block)

    def generate(self):
        """Generates the address decoder."""
        if not self._addresses:
            return None
        return self._tple.apply_str_to_str(
            match_template(
                self._num_bits,
                self._addresses,
                self._optimize),
            postprocess=False)

    def append_to_template(self, template_engine, key, comment):
        """Appends this decoder to the given template engine as a block,
        prefixing the given comment."""
        block = self.generate()
        if block is None:
            return
        template_engine.append_block(key, '@ ' + comment, block)


class RegfileGenerator:
    """VHDL generator for register files."""

    def __init__(self, regfile):
        """Constructs a VHDL generator for the given register file."""
        super().__init__()
        self._regfile = regfile

        # Main template engine, used to generate the actual VHDL files.
        self._tple = TemplateEngine()
        self._tple['r'] = regfile

        # Interface variables.
        self._public_types = []
        self._generic_decls = OrderedDict()
        self._port_decls = OrderedDict()

        # Address decoder builders.
        self._read_decoder = _Decoder('r_addr', 32)
        self._read_tag_decoder = _Decoder('r_rtag', regfile.read_tag_width)
        self._write_decoder = _Decoder('w_addr', 32)
        self._write_tag_decoder = _Decoder('w_rtag', regfile.write_tag_width)

        # Generate code for interrupts.
        for interrupt in regfile.interrupts:
            interrupt.generate_vhdl(self)

        # Generate boilerplate register access code before field code.
        for register in regfile.registers:
            self._add_register_boilerplate(register, 'before')

        # Generate code for fields.
        for field_descriptor in regfile.field_descriptors:
            field_descriptor.logic.generate_vhdl(self)

        # Generate boilerplate register access code before after code.
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

    def generate_files(self, output_directory):
        """Generates the files for this register file in the specified
        directory."""
        self._tple.apply_file_to_file(
            os.path.dirname(__file__) + os.sep + 'entity.template.vhd',
            output_directory + os.sep + self._regfile.meta.name + '.vhd',
            comment='-- ')
        self._tple.apply_file_to_file(
            os.path.dirname(__file__) + os.sep + 'package.template.vhd',
            output_directory + os.sep + self._regfile.meta.name + '_pkg.vhd',
            comment='-- ')

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

    def _add_interface(self, desc, name, typ, array, mode):
        """Adds an interface (port or generic) to the generated entity. `desc`
        must be a user-friendly string description of the interrupt or field
        that the interface belongs to; it is used as a comment. `name` must be
        a unique identifier within the entity for the interface. `typ` must be
        a `types._Base`-derived type description for the interface. `array`
        must be `None` if the interrupt/field is scalar, or the integral size
        of the array. `mode` must be `'in'`, `'out'`, or `'generic'` to select
        the interface type."""

        # If we need to make an array of signals/generics because the field or
        # interrupt we're generating for is a vector, modify the type
        # appropriately. If it is already an incomplete array, set its size
        # in-place; if it's not, build an incomplete array type around it.
        # If we don't want a vector but the user supplied an incomplete array,
        # just make an array with one entry.
        if array is not None and not typ.incomplete:
            typ = Array(typ.name, typ)
        if typ.incomplete:
            if array is None:
                array = 1

        # Store the type, so we can generate the requisite type definitions for
        # it later.
        self._public_types.append(typ)

        # Construct the generic/signal declaration and its abstracted Python
        # object representation for referring to it.
        decl, ref = {
            'generic': typ.make_generic,
            'in': typ.make_input,
            'out': typ.make_output,
        }[mode](name, array)

        # Construct the block comment from the block description and select the
        # appropriate dictionary to append to.
        if mode == 'generic':
            comment = '@ Generics for %s' % desc
            decl_dict = self._generic_decls
        else:
            comment = '@ Ports for %s' % desc
            decl_dict = self._port_decls

        # If there is no block with the specified comment yet, create one.
        # Otherwise, append to the previously created block.
        decls = decl_dict.get(comment, None)
        if decls is None:
            decl_dict[comment] = [decl]
        else:
            decls.append(decl)

        return ref

    def add_interrupt_interface(self, interrupt, name, typ, mode):
        """Registers a port or generic for the given interrupt with the
        specified (namespaced) name, VHDL type object (from `.types`), and
        mode, which must be `'in'`, `'out'`, or `'generic'`. Returns a
        pythonic object representing the interface (i.e., if the type is a
        record, it has attributes for each record entry; if it is an array, it
        can be indexed) that has a `__str__` function that converts to the VHDL
        name."""
        return self._add_interface(
            self._describe_interrupt(interrupt),
            'i_%s_%s' % (interrupt.meta.name, name),
            typ, interrupt.width, mode)

    def add_field_interface(self, field_descriptor, name, typ, mode):
        """Registers a port or generic for the given field descriptor with the
        specified (namespaced) name, VHDL type object (from `.types`), and
        mode, which must be `'in'`, `'out'`, or `'generic'`. Returns a
        pythonic object representing the interface (i.e., if the type is a
        record, it has attributes for each record entry; if it is an array, it
        can be indexed) that has a `__str__` function that converts to the VHDL
        name."""
        return self._add_interface(
            self._describe_field_descriptor(field_descriptor),
            'f_%s_%s' % (field_descriptor.meta.name, name),
            typ, field_descriptor.vector_count, mode)

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
        whether the interrupt(s) is/are asserted by writing to the variable
        expanded by `$irq$`. This is an `std_logic` for scalar interrupts, and
        an `std_logic_vector` for vector interrupts. It is active high."""
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

    def _add_field_bus_logic(self, field, direction, normal, lookahead, deferred):
        """Implements `add_field_read_logic()` and `add_field_write_logic()`.
        They are distinguished through `direction`, which must be `'r'` or
        `'w'`."""

        # Determine the address that the regular field logic should be
        # activated for.
        register = field.register
        address = register.address
        if direction == 'w':
            address += (1 << register.block_size) * (register.block_count - 1)
        mask = (1 << register.block_size) - 1

        # Describe the field for use in comments.
        desc = self._describe_field(field)

        # Add the normal and lookahead blocks.
        tple = TemplateEngine()
        tple['desc'] = desc
        tple['dir'] = direction
        if normal is not None:
            tple.append_block('NORMAL', '@ Access logic.', normal)
        if lookahead is not None:
            tple.append_block('LOOKAHEAD', '@ Lookahead logic.', lookahead)
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
                    desc, deferred),
                tag)

    def add_field_read_logic(self, field, normal, lookahead=None, deferred=None):
        """Registers code blocks for handling bus reads for the given field.
        Note that this function expects a `Field`, not a `FieldDescriptor`. The
        generator ensures that the generated code is only executed when the
        field is addressed, enabled, and the bus logic is performing the
        following actions:

         - `normal`: the bus is currently accessing the field, and the bus
           response buffers are ready to accept the read result. `r_prot` holds
           the protection flags for the read. The block can do the following
           things to interact with the bus:

            - Set `r_ack` to `true` and the bits in `r_hold` designated by the
              field's bitrange to the read result to acknowledge the request.
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

            - Set `r_ack` to `true` and the bits in `r_hold` designated by the
              field's bitrange to the read result to complete the transfer.
            - Set `r_nack` to `true` to respond with a slave error.
            - Set `r_block` to `true` to stall, IF the `can_block` flag was
              set for the field's read capabilities. In this case, the block
              will be executed again the next cycle.
            - Nothing: the bus behaves as if the field does not exist. If there
              are no other fields in the addressed register, a decode error is
              returned.
        """
        self._add_field_bus_logic(field, 'r', normal, lookahead, deferred)

    def add_field_write_logic(self, field, normal, lookahead=None, deferred=None):
        """Registers code blocks for handling bus writes for the given
        field. Note that this function expects a `Field`, not a
        `FieldDescriptor`. The generator ensures that the generated code is
        only executed when the register that the field belongs to is addressed,
        enabled, and the bus logic is performing the following actions:

         - `normal`: the bus is currently writing to the register that the
           field belongs to, and the bus response buffers are ready to accept
           the write result. `w_hold` and `w_hstb` hold the data that is being
           written to the register; the field should concern itself only with
           the bits in these variables designated by the field's bitrange. The
           variables carry the following significance:

            - `w_hstb` low, `w_hold` low: bit was not written/was masked out.
            - `w_hstb` high, `w_hold` low: bit was written zero.
            - `w_hstb` high, `w_hold` high: bit was written one.

           Note that it is possible that none of the bits belonging to the
           field were actually written; if the field wishes to honor the strobe
           bits, it must do so manually. `w_prot` furthermore holds the
           protection flags for the write. The block can do the following
           things to interact with the bus:

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
           fields that have a long access time. `w_hold`, `w_hstb`, and
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
        self._add_field_bus_logic(field, 'w', normal, lookahead, deferred)

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
        tple['cnt'] = register.block_count
        tple['read_tag'] = register.read_tag
        tple['write_tag'] = register.write_tag
        for block_index in range(register.block_count):
            tple['blk'] = register.block_count
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


class VhdlGenerator:
    """Class for generating VHDL from the register file descriptions."""

    def __init__(self, regfiles, output_directory):
        for regfile in regfiles:
            RegfileGenerator(regfile).generate_files(output_directory)
        with open(os.path.dirname(__file__) + os.sep + 'vhdmmio_pkg.vhd', 'r') as in_fd:
            vhdmmio_pkg = in_fd.read()
        with open(output_directory + os.sep + 'vhdmmio_pkg.vhd', 'w') as out_fd:
            out_fd.write(vhdmmio_pkg)
