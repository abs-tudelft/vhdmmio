"""Module for generating HTML documentation of the register files."""

import os
from markdown2 import Markdown
from vhdmmio.core.bitrange import BitRange

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
                bitrange = BitRange(
                    field.bitrange.bus_width,
                    address,
                    field.bitrange.size,
                    *bitrange_args)

                tooltip = '%s (%s)<br/>= %s' % (bitrange.to_spec(), field_mode, long_name)

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

def generate(regfiles, output_directory=None):
    """Generates HTML documentation for the given register files."""
    if output_directory is None:
        output_directory = '.'
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
