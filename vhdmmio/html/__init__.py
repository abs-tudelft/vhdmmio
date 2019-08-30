"""Module for generating HTML documentation of the register files."""

import os
from os.path import join as pjoin
import shutil
from markdown2 import Markdown
from ..version import __version__
from ..core.address import AddressSignalMap
from ..template import TemplateEngine, annotate_block

_MODULE_DIR = os.path.dirname(__file__)

_SECTION = annotate_block("""
<div class="content">
  $header$
$ BRIEF
$if defined('EXTENDED')
  <div class="extended">
$   EXTENDED
  </div>
$endif
</div>
""", comment='--')


_BITMAP_TABLE = annotate_block("""
<table class="bitmap">
  <thead>
    <th>Address</th>
$if any_conditions
    <th>Conditions</th>
$endif
    <th>Name</th>
    <th class="bitmap-last-col-header">Mode</th>
$   BITS
  </thead>
  <tbody>
$   BODY
  </tbody>
</table>
""")


class DocumentationFlags:
    """Maintains a set of documentation "flags", which can then be coverted to
    HTML to be put at the top of the documentation section for an object. In
    this context, flags are just short pieces of text or icons with a title
    text containing more info, to quickly let the user see the features of some
    object, a bit like badges at the top of a readme file on github."""

    def __init__(self):
        super().__init__()
        self._flags = []

    def append(self, cls, brief, name, extended):
        """Adds a flag."""
        brief = str(brief)
        self._flags.append((cls, brief, name, extended.format(brief=brief)))

    def to_html(self):
        """Converts the flags to HTML."""
        html = ['<ul class="flags">']
        for cls, brief, name, extended in self._flags:
            html.append(
                '  <li class="flag-%s">\n'
                '    <span class="tooltip-left">\n'
                '      %s\n'
                '      <span class="tooltiptext">\n'
                '        %s\n'
                '        <p>%s</p>\n'
                '      </span>\n'
                '    </span>\n'
                '  </li>' % (
                    cls, brief, name,
                    extended.replace('&', '&amp;').replace('"', '&quot;')))
        html.append('</ul>')
        return '\n'.join(html)


class HtmlDocumentationGenerator:
    """Generator for HTML documentation."""

    def __init__(self, regfiles):
        super().__init__()
        self._regfiles = regfiles
        self._markdowner = Markdown(extras=["tables"])

    def _md_to_html(self, markdown, depth=0):
        """Converts markdown to HTML."""
        return self._markdowner.convert(markdown.replace('\n#', '\n#' + '#'*depth))

    def _generate_bitmap_table(self, blocks):
        """Generates a table with addresses on the Y axis and bus word bit
        indices on the X axis for the specified block(s)."""
        any_conditions = False
        for block in blocks:
            _, conditions = block.doc_address()
            if conditions:
                any_conditions = True
                break

        bus_width = blocks[0].register.regfile.cfg.features.bus_width

        tple = TemplateEngine()
        tple['any_conditions'] = any_conditions
        tple.append_block('BITS', '\n'.join(
            '<th class="bitmap-bit">%d</th>' % bit for bit in reversed(range(bus_width))))

        prev_address = None
        odd = True
        for block in blocks:
            row = []

            # Construct per-block header columns.
            if block.row_count > 1:
                attributes = ' rowspan="%s"' % block.row_count
            else:
                attributes = ''
            bus_address, conditions = block.doc_address()
            row.append('<td%s>%s</td>' % (attributes, bus_address))
            if any_conditions:
                if conditions:
                    row.append('<td%s>%s</td>' % (attributes, ', '.join(conditions)))
                else:
                    row.append('<td%s class="de-emph">n/a</td>' % attributes)

            cell_fmt = (
                '<td%s><div class="tooltip-left">\n'
                '  %s\n'
                '  <span class="tooltiptext">\n'
                '    %s %s (%s)\n'
                '    %s\n'
                '  </span>\n'
                '</div></td>')

            if not block.can_write():
                mode = 'R/O'
            elif not block.can_read():
                mode = 'W/O'
            else:
                mode = 'R/W'

            if len(block.register.blocks) == 1:
                row.append(cell_fmt % (
                    attributes, block.register.mnemonic,
                    'Logical register', bus_address, mode,
                    self._md_to_html('`%s` (`%s`): %s' % (
                        block.register.name, block.register.mnemonic, block.register.brief))))
            else:
                row.append(cell_fmt % (
                    attributes, block.mnemonic,
                    'Block', bus_address, mode,
                    self._md_to_html('`%s` (`%s`): %s\n\nLogical register `%s` (`%s`): %s' % (
                        block.name, block.mnemonic, block.brief,
                        block.register.name, block.register.mnemonic, block.register.brief))))

            # Construct per-row header column.
            rows = []
            for row_header in block.row_headers:
                row.append('<td class="bitmap-last-col-header">%s</td>' % row_header)
                rows.append(row)
                row = []

            # Construct table content.
            current_col = 0
            current_row = 0

            def insert_cell(content=None, col_span=1, row_span=1):
                if not col_span or not row_span:
                    return
                html = ['<td']
                if col_span > 1:
                    html.append(' colspan="%d"' % col_span)
                if row_span > 1:
                    html.append(' rowspan="%d"' % row_span)
                if content is None:
                    html.append(' class="bitmap-reserved"')
                    content = '&nbsp;'
                else:
                    html.append(' class="bitmap-mapping"')
                html.append('>%s</td>' % content)

                # The variables below that the linter is complaining about are
                # safe to use here, because we don't use this closure outside
                # of the loop body we defined it in.
                rows[current_row].append(''.join(html)) #pylint: disable=W0640

            for mapping in block.mappings:
                assert mapping.row_index >= current_row
                while mapping.row_index > current_row:
                    insert_cell(col_span=block.col_count - current_col)
                    current_col = 0
                    current_row += 1
                assert mapping.col_index >= current_col
                insert_cell(col_span=mapping.col_index - current_col)

                field = mapping.field

                if not field.bitrange.is_vector():
                    bus_indices = ':%d' % mapping.offset
                    field_indices = ''
                elif mapping.col_span > 1:
                    bus_indices = ':%d..%d' % (
                        mapping.offset + mapping.col_span - 1, mapping.offset)
                    field_indices = ':%d..%d' % (mapping.high, mapping.low)
                else:
                    bus_indices = ':%d' % mapping.offset
                    field_indices = ':%d' % mapping.low
                if field.bitrange.width == mapping.col_span:
                    field_indices = ''

                if not field.behavior.bus.can_write():
                    field_mode = 'R/O'
                elif not field.behavior.bus.can_read():
                    field_mode = 'W/O'
                else:
                    field_mode = 'R/W'

                abbreviated = '%s%s' % (field.mnemonic, field_indices)

                if len(abbreviated) > mapping.col_span*4-1:
                    abbreviated = abbreviated[:mapping.col_span*4-2] + '…'
                else:
                    abbreviated = abbreviated

                cell = (
                    '<div class="tooltip-right">\n'
                    '  %s\n'
                    '  <span class="tooltiptext">\n'
                    '    Field %s%s (%s)\n'
                    '    %s\n'
                    '  </span>\n'
                    '</div>' % (
                        abbreviated,
                        bus_address, bus_indices, field_mode,
                        self._md_to_html('`%s%s` (`%s%s`): %s' % (
                            field.name, field_indices,
                            field.mnemonic, field_indices,
                            field.brief))))

                insert_cell(cell, col_span=mapping.col_span, row_span=mapping.row_span)
                current_col = mapping.col_index + mapping.col_span

            insert_cell(col_span=block.col_count - current_col)

            if odd:
                tr_class = 'odd'
            else:
                tr_class = 'even'
            odd = not odd

            address = block.address
            if prev_address is not None and prev_address + 1 < address:
                tr_class += ' bitmap-restart'
            prev_address = address

            tple.append_block('BODY', '\n'.join((
                '<tr class="%s">\n  %s\n</tr>' % (tr_class, '\n  '.join(row)) for row in rows)))
        return tple.apply_str_to_str(_BITMAP_TABLE)

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
        flags = DocumentationFlags()

        # Add bitrange flag.
        flags.append(
            'bitrange', field.bitrange, 'Bitrange',
            'This field is located at bit {brief} of the logical register.')

        # Add reset value flag.
        if field.behavior.doc_reset is None:
            flags.append(
                'reset', '-', 'Reset value',
                'The reset value is undefined or unknown.')
        else:
            if field.bitrange.width > 8:
                reset = '0x%0*X' % ((field.bitrange.width + 3) // 4, field.behavior.doc_reset)
            else:
                reset = ('{:0%db}' % field.bitrange.width).format(field.behavior.doc_reset)
            flags.append(
                'reset', reset, 'Reset value',
                'The reset value is {brief}.')

        # Add bus access mode flag.
        if field.behavior.bus.can_read() and field.behavior.bus.can_write():
            flags.append(
                'mode', 'R/W', 'Access mode',
                'This field is read/write.')
        elif field.behavior.bus.can_write():
            flags.append(
                'mode', 'W/O', 'Access mode',
                'This field is write-only.')
        else:
            flags.append(
                'mode', 'R/O', 'Access mode',
                'This field is read-only.')

        # Add behavior class flag.
        flags.append(
            'type', field.cfg.behavior, 'Behavior',
            'This field has "{brief}" behavior, excluding modifications.')

        # Add privilege flag if nonstandard.
        def decode_prot(bus_access_behavior):
            if bus_access_behavior is None:
                return '0', 'not %s'
            prot = bus_access_behavior.prot_mask

            brief = ''
            ext = []

            if prot[0] == '-':
                brief += '-'
            elif prot[0] == '0':
                brief += 'D'
                ext.append('data')
            elif prot[0] == '1':
                brief += 'I'
                ext.append('instruction')

            if prot[1] == '-':
                brief += '-'
            elif prot[1] == '0':
                brief += 'S'
                ext.append('secure')
            elif prot[1] == '1':
                brief += 'N'
                ext.append('non-secure')

            if prot[2] == '-':
                brief += '-'
            elif prot[2] == '0':
                brief += 'U'
                ext.append('user/unprivileged')
            elif prot[2] == '1':
                brief += 'P'
                ext.append('privileged')

            if not ext:
                ext = '%s using any transfer'
            else:
                ext = 'only %%s using %s transfers' % ', '.join(ext)

            return brief, ext

        read_brief, read_ext = decode_prot(field.behavior.bus.read)
        write_brief, write_ext = decode_prot(field.behavior.bus.write)
        if read_brief not in ('0', '---') or write_brief not in ('0', '---'):
            if read_brief == '0' or write_brief == '0' or read_brief == write_brief:
                prot_brief = read_brief
                read_ext %= 'accessible'
                prot_ext = 'This field is only %s.' % read_ext
            else:
                prot_brief = '%s/%s' % (read_brief, write_brief)
                read_ext %= 'readable'
                write_ext %= 'writable'
                prot_ext = 'This field is only %s, and %s.' % (read_ext, write_ext)
            flags.append('privileges', prot_brief, 'Protection', prot_ext)

        tple.append_block('BRIEF', flags.to_html())

        # Add user-provided brief.
        tple.append_block('BRIEF', self._named_brief_to_html(field))

        # Add user-provided extended documentation.
        if field.doc is not None:
            tple.append_block('EXTENDED', self._md_to_html(field.doc, depth))

        return tple.apply_str_to_str(_SECTION)

    def _register_to_html(self, register, depth=1):
        """Generates the documentation section for the given register."""
        tple = TemplateEngine()
        tple['header'] = self._named_header_to_html(register, depth)
        flags = DocumentationFlags()

        # Add address information flags.
        bus_address, conditions = register.doc_address()
        flags.append(
            'address', bus_address, 'Address',
            'This register is located at bus address {brief}.')
        for condition in conditions:
            flags.append(
                'condition', condition, 'Conditions',
                'Additional address match condition: {brief}.')

        # Add bus access mode flag.
        if register.can_read() and register.can_write():
            flags.append(
                'mode', 'R/W', 'Access mode',
                'This register is read/write.')
        elif register.can_write():
            flags.append(
                'mode', 'W/O', 'Access mode',
                'This register is write-only.')
        else:
            flags.append(
                'mode', 'R/O', 'Access mode',
                'This register is read-only.')

        # Add endianness flag if the register has multiple blocks.
        if register.little_endian:
            flags.append(
                'endianness', 'LE', 'Endianness',
                'This is a %d-block little-endian compound register.'
                % len(register.blocks))
        if register.big_endian:
            flags.append(
                'endianness', 'BE', 'Endianness',
                'This is a %d-block big-endian compound register.'
                % len(register.blocks))

        tple.append_block('BRIEF', flags.to_html())

        # Add user-provided brief.
        tple.append_block('BRIEF', self._named_brief_to_html(register))

        # Add user-provided extended documentation.
        if register.doc is not None:
            tple.append_block('EXTENDED', self._md_to_html(register.doc, depth))

        # Add the bitmap table for this register.
        tple.append_block('EXTENDED', self._generate_bitmap_table(register.blocks))

        # Add documentation for the fields.
        for field in register.fields:
            tple.append_block('EXTENDED', self._field_to_html(field, depth + 1))

        return tple.apply_str_to_str(_SECTION)

    def _interrupt_to_html(self, interrupt, depth=1):
        """Generates the documentation section for the given interrupt."""
        tple = TemplateEngine()
        tple['header'] = self._named_header_to_html(interrupt, depth)
        flags = DocumentationFlags()

        # Add interrupt type flag.
        if interrupt.level_sensitive:
            irq_type = 'level-%s' % interrupt.active
        elif interrupt.active in ('high', 'low'):
            irq_type = 'strobe-%s' % interrupt.active
        else:
            irq_type = str(interrupt.active)
        flags.append(
            'type', irq_type, 'Interrupt sensitivity',
            'The trigger condition for this interrupt is {brief}.')

        tple.append_block('BRIEF', flags.to_html())

        # Add user-provided brief.
        tple.append_block('BRIEF', self._named_brief_to_html(interrupt))

        # Add user-provided extended documentation.
        if interrupt.doc is not None:
            tple.append_block('EXTENDED', self._md_to_html(interrupt.doc, depth))

        return tple.apply_str_to_str(_SECTION)

    def _regfile_to_html(self, regfile, depth=1):
        """Generates the documentation section for the given register file."""
        tple = TemplateEngine()
        tple['header'] = self._named_header_to_html(regfile, depth)

        # Add user-provided brief.
        tple.append_block('BRIEF', self._named_brief_to_html(regfile))

        # Construct a list of all the address blocks ordered by address.
        blocks = []
        for _, _, read_block, write_block in regfile.doc_iter_blocks():
            if read_block is write_block:
                blocks.append(read_block)
                continue
            if read_block is not None:
                blocks.append(read_block)
            if write_block is not None:
                blocks.append(write_block)

        # Add the bitmap table for this register.
        tple.append_block('BRIEF', self._generate_bitmap_table(blocks))

        # Add user-provided extended documentation.
        if regfile.doc is not None:
            tple.append_block('EXTENDED', self._md_to_html(regfile.doc, depth))

        # Add documentation for the fields.
        for block in blocks:
            if block.index:
                continue
            register = block.register
            tple.append_block('EXTENDED', self._register_to_html(register, depth + 1))

        # Add documentation for the interrupts.
        for interrupt in regfile.interrupts:
            tple.append_block('EXTENDED', self._interrupt_to_html(interrupt, depth + 1))

        return tple.apply_str_to_str(_SECTION)

    def generate(self, output_dir):
        """Generates the HTML documentation files for the register files in the
        given directory."""
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        tple = TemplateEngine()
        for regfile in self._regfiles:
            tple.append_block('BODY', self._regfile_to_html(regfile))
        tple['title'] = 'Register file documentation'
        tple['version'] = __version__
        tple.apply_file_to_file(
            pjoin(_MODULE_DIR, 'base.template.html'),
            pjoin(output_dir, 'index.html'))
        tple.apply_file_to_file(
            pjoin(_MODULE_DIR, 'style.template.css'),
            pjoin(output_dir, 'style.css'))
