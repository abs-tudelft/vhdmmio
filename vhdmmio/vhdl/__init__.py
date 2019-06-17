"""Module for generating VHDL from the register file descriptions."""

import os
import re
from vhdmmio.template import TemplateEngine
from .match import match_template

_REGISTER_READ = '''
$if blk == 0 and defined('FIELD_LOOKAHEAD')
if r_lreq then
$ FIELD_LOOKAHEAD
end if;
$endif
if r_req then
$if blk == 0 and defined('FIELD_NORMAL')
$ FIELD_NORMAL
$endif
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
'''

_REGISTER_WRITE = '''
if w_req then
  w_hold($bw*blk + bw-1$ downto $bw*blk$) := w_data;
  w_hstb($bw*blk + bw-1$ downto $bw*blk$) := w_strb;
$if blk < cnt - 1
  w_multi := '1';
$else
  w_multi := '0';
$endif
$if blk == cnt - 1 and defined('FIELD_NORMAL')
$ FIELD_NORMAL
$endif
end if;
$if blk == cnt - 1 and defined('FIELD_LOOKAHEAD')
if w_lreq then
$ FIELD_LOOKAHEAD
end if;
$endif
'''

def _append(engine, tag, block):
    """Shorthand for appending a block to the given template engine if it is
    not empty."""
    if block:
        engine.append_block(tag, block)

def _generate_interrupts(tple, regfile):
    """Generates the logic for the interrupts in `regfile` and appends it to
    `TemplateEngine` `tple`."""
    for interrupt in regfile.interrupts:
        comment = interrupt.meta[None].markdown_brief
        assert '\n' not in comment
        if interrupt.can_clear:
            comment = '@ Edge-sensitive: ' + comment
        else:
            comment = '@ Level-sensitive: ' + comment
        if interrupt.width is None:
            tple.append_block(
                'PORTS', comment,
                'irq_%s : in std_logic := \'0\';' % interrupt.meta.name)
            irq_range = '%d' % interrupt.index
        else:
            tple.append_block(
                'PORTS', comment,
                'irq_%s : in std_logic_vector(%d downto 0) '
                ':= (others => \'0\');' % (interrupt.meta.name, interrupt.width - 1))
            irq_range = '%d downto %d' % (interrupt.high, interrupt.low)
        if interrupt.can_clear:
            tple.append_block(
                'IRQ_LOGIC', comment,
                'i_flag({1}) := i_flag({1}) or (irq_{0} and i_enab({1});'
                .format(interrupt.meta.name, irq_range))
        else:
            tple.append_block(
                'IRQ_LOGIC', comment,
                'i_flag({1}) := irq_{0} and i_enab({1});'
                .format(interrupt.meta.name, irq_range))

def _generate_address_decoder(tple, regfile, mode):
    """Generates the `<mode>_addr` decoder for `regfile` and appends it to
    `TemplateEngine` `tple`."""
    access_tple = TemplateEngine()
    access_tple['address'] = mode + '_addr'
    addresses = []
    for register in regfile.registers:
        if register.read_caps if mode == 'r' else register.write_caps is not None:
            for block_index in range(register.block_count):
                address = (
                    register.address + (1 << register.block_size) * block_index,
                    (1 << register.block_size) - 1)
                addresses.append(address)

                reg_tple = TemplateEngine()
                reg_tple['blk'] = block_index
                reg_tple['cnt'] = register.block_count
                reg_tple['bw'] = regfile.bus_width

                if mode == 'r':
                    for field in register.fields:
                        _append(reg_tple, 'FIELD_NORMAL',
                                field.logic.generate_vhdl_read(field.index))
                        _append(reg_tple, 'FIELD_LOOKAHEAD',
                                field.logic.generate_vhdl_read_lookahead(field.index))
                    block = reg_tple.apply_str_to_str(
                        _REGISTER_READ, postprocess=False)
                else:
                    for field in register.fields:
                        _append(reg_tple, 'FIELD_NORMAL',
                                field.logic.generate_vhdl_write(field.index))
                        _append(reg_tple, 'FIELD_LOOKAHEAD',
                                field.logic.generate_vhdl_write_lookahead(field.index))
                    block = reg_tple.apply_str_to_str(
                        _REGISTER_WRITE, postprocess=False)

                if mode == 'r':
                    comment = 'Read logic for '
                else:
                    comment = 'Write logic for '
                comment += '%s (%s)' % (register.meta.name, register.meta.mnemonic)
                if register.block_count > 1:
                    comment += ', multi-word %d/%d' % (block_index+1, register.block_count)
                block = '@ %s.\n%s' % (comment, block)

                _append(access_tple, 'ADDR_0x%X' % address[0], block)

    access_block = access_tple.apply_str_to_str(
        match_template(32, addresses, True), postprocess=False)
    if mode == 'r':
        access_block = '@ Read address decoder.\n%s' % access_block
        _append(tple, 'FIELD_LOGIC_READ', access_block)
    else:
        access_block = '@ Write address decoder.\n%s' % access_block
        _append(tple, 'FIELD_LOGIC_WRITE', access_block)

def _generate_tag_decoder(tple, regfile, mode):
    """Generates the `<mode>_dtag` decoder for `regfile` and appends it to
    `TemplateEngine` `tple`."""
    if mode == 'r':
        if not regfile.read_tag_count:
            return
    else:
        if not regfile.write_tag_count:
            return

    # TODO
    raise NotImplementedError()

def _generate_fields(tple, regfile):
    """Generates the logic for the fields in `regfile` and appends it to
    `TemplateEngine` `tple`."""
    for field_descriptor in regfile.field_descriptors:
        _append(tple, 'GENERICS', field_descriptor.logic.generate_vhdl_generics())
        _append(tple, 'PORTS', field_descriptor.logic.generate_vhdl_ports())
        _append(tple, 'FIELD_VARIABLES', field_descriptor.logic.generate_vhdl_variables())
        _append(tple, 'FIELD_LOGIC_BEFORE', field_descriptor.logic.generate_vhdl_before_bus())
        _append(tple, 'FIELD_LOGIC_AFTER', field_descriptor.logic.generate_vhdl_after_bus())
        _append(tple, 'PACKAGE', field_descriptor.logic.generate_vhdl_package())
        _append(tple, 'PACKAGE_BODY', field_descriptor.logic.generate_vhdl_package_body())

    for mode in 'rw':
        _generate_address_decoder(tple, regfile, mode)
        _generate_tag_decoder(tple, regfile, mode)

def _populate_template(tple, regfile):
    tple['r'] = regfile
    _generate_interrupts(tple, regfile)
    _generate_fields(tple, regfile)

class VhdlGenerator:
    """Class for generating VHDL from the register file descriptions."""

    def __init__(self, regfiles, output_dir):
        for regfile in regfiles:
            tple = TemplateEngine()
            _populate_template(tple, regfile)

            tple.apply_file_to_file(
                os.path.dirname(__file__) + os.sep + 'entity.template.vhd',
                output_dir + os.sep + regfile.meta.name + '.vhd',
                comment='-- ')
            tple.apply_file_to_file(
                os.path.dirname(__file__) + os.sep + 'package.template.vhd',
                output_dir + os.sep + regfile.meta.name + '_pkg.vhd',
                comment='-- ')

        with open(os.path.dirname(__file__) + os.sep + 'vhdmmio_pkg.vhd', 'r') as in_fd:
            vhdmmio_pkg = in_fd.read()
        with open(output_dir + os.sep + 'vhdmmio_pkg.vhd', 'w') as out_fd:
            out_fd.write(vhdmmio_pkg)
