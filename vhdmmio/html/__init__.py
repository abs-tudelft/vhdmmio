"""Module for generating HTML documentation of the register files."""

import os
from os.path import join as pjoin
import shutil
from markdown2 import Markdown
from ..core.address import AddressSignalMap
from ..template import TemplateEngine, annotate_block

_MODULE_DIR = os.path.dirname(__file__)

_SECTION = annotate_block("""
$header$
$if defined('EXTENDED')
<div class="brief">
$ BRIEF
</div>
<div class="extended">
$ EXTENDED
</div>
$else
$BRIEF
$endif
""", comment='--')


class DocumentationFlags:
    """Maintains a set of documentation "flags", which can then be coverted to
    HTML to be put at the top of the documentation section for an object. In
    this context, flags are just short pieces of text or icons with a title
    text containing more info, to quickly let the user see the features of some
    object, a bit like badges at the top of a readme file on github."""

    def __init__(self):
        super().__init__()
        self._flags = []

    def append(self, cls, brief, extended):
        """Adds a flag."""
        self._flags.append((cls, brief, extended))

    def to_html(self):
        """Converts the flags to HTML."""
        html = ['<ul class="flags">']
        for cls, brief, extended in self._flags:
            html.append('  <li class="flag-%s" title="%s">%s</li>' % (
                cls, extended.replace('&', '&amp;').replace('"', '&quot;'), brief))
        html.append('</ul>')
        return '\n'.join(html)


class HtmlDocumentationGenerator:
    """Generator for HTML documentation."""

    def __init__(self, regfiles):
        super().__init__()
        self._regfiles = regfiles
        self._markdowner = Markdown(extras=["tables"])

    def _md_to_html(self, markdown):
        """Converts markdown to HTML."""
        return self._markdowner.convert(markdown)

    @staticmethod
    def _named_header_to_html(named, depth=1):
        """Generates a HTML header for the given `Named`."""
        if named.mnemonic == named.name.upper():
            name = '<code>%s</code>' % (named.name,)
        else:
            name = '<code>%s</code> (<code>%s</code>)' % (named.name, named.mnemonic)
        typ = named.get_type_name()
        typ = typ[0].upper() + typ[1:]
        return '<h%d>%s %s</h%d>' % (depth, typ, name, depth)

    def _named_brief_to_html(self, named):
        """Generates the HTML for the brief documentation of the given
        `Named`."""
        brief_md = named.brief[0].upper() + named.brief[1:]
        return self._md_to_html(brief_md)

    def _field_to_html(self, field, depth=1):
        """Generates the documentation section for the given field."""
        tple = TemplateEngine()
        tple['header'] = self._named_header_to_html(field, depth)
        tple.append_block('BRIEF', self._named_brief_to_html(field))
        if field.doc is not None:
            tple.append_block('EXTENDED', self._md_to_html(field.doc))
        return tple.apply_str_to_str(_SECTION)

    def _register_to_html(self, subaddresses, register, depth=1):
        """Generates the documentation section for the given register."""
        tple = TemplateEngine()
        tple['header'] = self._named_header_to_html(register, depth)

        flags = DocumentationFlags()

        # Add address information flags.
        for signal, subaddress in subaddresses.items():
            subaddress = subaddress.doc_represent(signal.width)
            if signal is AddressSignalMap.BUS:
                flags.append(
                    'address',
                    subaddress,
                    'This register is located at bus address %s.' % subaddress)
            elif subaddress != '-':
                flags.append(
                    'condition',
                    '%s=%s' % (signal.name, subaddress),
                    'Additional address match condition: %s = %s.' % (signal, subaddress))

        # Add bus access mode flag.
        if register.can_read() and register.can_write():
            flags.append('access', 'R/W', 'This register is read/write.')
        elif register.can_write():
            flags.append('access', 'W/O', 'This register is write-only.')
        else:
            flags.append('access', 'R/O', 'This register is read-only.')

        # Add endianness flag if the register has multiple blocks.
        if register.little_endian:
            flags.append(
                'endian', 'LE',
                'This is a %d-block little-endian compound register.'
                % len(register.blocks))
        if register.big_endian:
            flags.append(
                'endian', 'BE',
                'This is a %d-block big-endian compound register.'
                % len(register.blocks))

        tple.append_block('BRIEF', flags.to_html())
        tple.append_block('BRIEF', self._named_brief_to_html(register))
        if register.doc is not None:
            tple.append_block('EXTENDED', self._md_to_html(register.doc))

        for field in register.fields:
            tple.append_block('EXTENDED', self._field_to_html(field, depth + 1))

        return tple.apply_str_to_str(_SECTION)

    def _interrupt_to_html(self, interrupt, depth=1):
        """Generates the documentation section for the given interrupt."""
        tple = TemplateEngine()
        tple['header'] = self._named_header_to_html(interrupt, depth)
        tple.append_block('BRIEF', self._named_brief_to_html(interrupt))
        if interrupt.doc is not None:
            tple.append_block('EXTENDED', self._md_to_html(interrupt.doc))
        return tple.apply_str_to_str(_SECTION)

    def _regfile_to_html(self, regfile, depth=1):
        """Generates the documentation section for the given register file."""
        tple = TemplateEngine()
        tple['header'] = self._named_header_to_html(regfile, depth)
        tple.append_block('BRIEF', self._named_brief_to_html(regfile))
        if regfile.doc is not None:
            tple.append_block('EXTENDED', self._md_to_html(regfile.doc))

        for subaddresses, _, read_reg, write_reg in regfile.doc_iter_registers():
            if read_reg is write_reg:
                tple.append_block('EXTENDED', self._register_to_html(
                    subaddresses, read_reg, depth + 1))
            else:
                if read_reg is not None:
                    tple.append_block('EXTENDED', self._register_to_html(
                        subaddresses, read_reg, depth + 1))
                if write_reg is not None:
                    tple.append_block('EXTENDED', self._register_to_html(
                        subaddresses, write_reg, depth + 1))

        for interrupt in regfile.interrupts:
            tple.append_block('EXTENDED', self._interrupt_to_html(interrupt, depth + 1))

        return tple.apply_str_to_str(_SECTION)

    def generate(self, output_dir):
        """Generates the HTML documentation files for the register files in the
        given directory."""
        tple = TemplateEngine()
        for regfile in self._regfiles:
            tple.append_block('BODY', self._regfile_to_html(regfile))
        tple['title'] = 'TODO'
        tple.apply_file_to_file(
            pjoin(_MODULE_DIR, 'base.template.html'),
            pjoin(output_dir, 'index.html'))
        shutil.copyfile(
            pjoin(_MODULE_DIR, 'style.css'),
            pjoin(output_dir, 'style.css'))


# TODO: old code below here, to be removed

#get#xdg-open#to#interpret#this#as#a#python#file#...######
######################################################

_HEADER = """<!DOCTYPE html>
<html>
<meta charset="UTF-8">
<style>
.tooltip {
  position: relative;
  display: inline-block;
}

.tooltip .tooltiptext {
  visibility: hidden;
  width: 200px;
  background-color: black;
  color: #fff;
  text-align: center;
  border-radius: 6px;
  padding: 5px 0;
  position: absolute;
  z-index: 1;
  top: 150%;
  left: 50%;
  margin-left: -100px;
}

.tooltip .tooltiptext::after {
  content: "";
  position: absolute;
  bottom: 100%;
  left: 50%;
  margin-left: -5px;
  border-width: 5px;
  border-style: solid;
  border-color: transparent transparent black transparent;
}

.tooltip:hover .tooltiptext {
  visibility: visible;
}
</style>
"""

_FOOTER = """
</body>
</html>
"""

def _bitfield_table_body(address, read_bitmap, write_bitmap):
    def parse_bitmap(bitmap):
        prev_field = False
        cols = []
        for reg_index, (field, field_index) in enumerate(bitmap):
            if field is not prev_field:
                cols.append([field, reg_index, field_index, 1])
            else:
                cols[-1][3] += 1
            prev_field = field
        return tuple(reversed(list(map(tuple, cols))))

    read = parse_bitmap(read_bitmap)
    write = parse_bitmap(write_bitmap)
    rowspanned = set()
    if len(read) == 1 and read[0][0] is None:
        mode = ['W']
    elif len(write) == 1 and write[0][0] is None:
        mode = ['R']
    elif read == write:
        mode = ['R/W']
    else:
        mode = ['R', 'W']
        write_dict = {
            reg_index: (field, field_index, width)
            for field, reg_index, field_index, width in write}
        for field, reg_index, field_index, width in read:
            if field is None or reg_index not in write_dict:
                continue
            wr_field, wr_field_index, wr_width = write_dict[reg_index]
            if field is wr_field and field_index == wr_field_index and width == wr_width:
                rowspanned.add(reg_index)

    # Generate the first line.
    lines = []
    for line_nr, line_mode in enumerate(mode):
        html = ['<td>%s</td>' % line_mode]
        bitmap = read if line_mode.startswith('R') else write
        for field, reg_index, field_index, width in bitmap:
            if reg_index in rowspanned:
                if line_nr == 1:
                    continue
                height = 2
                field_mode = 'R/W'
            else:
                height = 1
                field_mode = line_mode
            html.append('<td colspan="%d" rowspan="%d">' % (width, height))
            if field is None:
                html.append('&nbsp;')
            else:
                name = field.meta.mnemonic
                if not field.bitrange.is_vector():
                    indices = ''
                elif width > 1:
                    indices = ':%d..%d' % (field_index + width - 1, field_index)
                else:
                    indices = ':%d' % field_index
                long_name = name + indices
                if width != field.bitrange.width:
                    name += indices

                if width == field.bitrange.bus_width:
                    bitrange_args = []
                elif width == 1:
                    bitrange_args = [reg_index]
                else:
                    bitrange_args = [reg_index + width - 1, reg_index]
                #bitrange = BitRange(
                    #field.bitrange.bus_width,
                    #address,
                    #field.bitrange.size,
                    #*bitrange_args) TODO
                _ = address, bitrange_args

                tooltip = '%s (%s)<br/>= %s' % ('bitrange.to_spec() TODO', field_mode, long_name)

                if len(name) > width*2:
                    abbreviated = name[:width*2-1] + '…'
                else:
                    abbreviated = name
                html.append(
                    '<code class="tooltip">%s<span class="tooltiptext">%s</span></code>' % (
                        abbreviated, tooltip))
            html.append('</td>')
        lines.append('\n'.join(html))

    return lines

def _bitfield_table(*registers):
    width = registers[0].regfile.bus_width
    lines = []
    lines.append('<table border=1>')
    lines.append('<tr>')
    lines.append('<th>Address</th>')
    lines.append('<th>Mode</th>')
    for bit in reversed(range(width)):
        lines.append('<th>%d</th>' % bit)
    lines.append('<th>Name</th>')
    lines.append('</tr>')

    for register in registers:
        body = []
        for block in range(register.block_count):
            address = register.address + (block << register.block_size)
            block_body = _bitfield_table_body(
                address,
                register.read_bitmap[block*width:(block+1)*width],
                register.write_bitmap[block*width:(block+1)*width])
            address = '0x%08X/%d' % (address, register.block_size)
            block_body[0] = '<td rowspan="%d">%s</td>\n%s' % (
                len(block_body), address, block_body[0])
            body.extend(block_body)
        body[0] += '\n<td rowspan="%d"><code>%s</code></td>' % (
            len(body), register.meta.mnemonic)
        for line in body:
            lines.append('<tr>\n%s\n</tr>' % line)

    lines.append('</table>')
    return '\n'.join(lines)

def generate(regfiles, output_directory):
    """Generates HTML documentation for the given register files. The files are
    written to the given output directory. If the output directory does not
    exist yet, it is first created."""
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
    fname = output_directory + os.sep + 'index.html'
    with open(fname, 'w') as out_fd:
        print(_HEADER, file=out_fd)
        markdowner = Markdown(extras=["tables"])
        for regfile in regfiles:
            print(markdowner.convert(regfile.meta.to_markdown(1)), file=out_fd)
            print(_bitfield_table(*regfile.registers), file=out_fd)
            for register in regfile.registers:
                print(markdowner.convert(register.meta.to_markdown(2)), file=out_fd)
                print(_bitfield_table(register), file=out_fd)
                for field in register.fields:
                    print(markdowner.convert(field.meta.to_markdown(3)), file=out_fd)
        print(_FOOTER, file=out_fd)
    print('Wrote %s' % fname)
