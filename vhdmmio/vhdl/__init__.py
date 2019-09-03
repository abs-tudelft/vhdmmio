"""Module for generating VHDL for the register files."""

import os
from os.path import join as pjoin
import shutil
from ..version import __version__
from ..core.address import AddressSignalMap
from ..core.subaddress import SubAddress
from ..template import TemplateEngine, annotate_block
from .types import Axi4Lite, gather_defs
from .interface import Interface
from .address_decoder import AddressDecoder
from .behavior import BehaviorCodeGen

_MODULE_DIR = os.path.dirname(__file__)


_INTERRUPT_TEMPLATE = annotate_block("""
|$if active == 'rising'
  |i_req($r$) := $i$ and not i_raw($r$);
|$endif
|$if active == 'falling'
  |i_req($r$) := i_raw($r$) and not $i$;
|$endif
|$if active == 'edge'
  |i_req($r$) := $i$ xor i_raw($r$);
|$endif
|i_raw($r$) := $i$;
|$if active == 'high'
  |i_req($r$) := $i$;
|$endif
|$if active == 'low'
  |i_req($r$) := not $i$;
|$endif
""")


_BLOCK_ACCESS_TEMPLATE = annotate_block("""
|$block BEFORE_READ_RESP
  |@ Clear holding register location prior to read.
  |r_hold := (others => '0');
|$endblock
|
|$block BEFORE_READ
  |$if blk_idx == 0
    |$if phase == 'request'
      |if r_req then
      |$ BEFORE_READ_RESP
      |end if;
    |$else
      |$BEFORE_READ_RESP
    |$endif
  |$endif
|$endblock
|
|$block AFTER_READ_RESP
  |r_data := r_hold($bw*word_idx + bw-1$ downto $bw*word_idx$);
  |$if blk_cnt > 1
    |$if blk_idx == 0
      |r_multi := '1';
    |$else
      |if r_multi = '1' then
      |  r_ack := true;
      |else
      |  r_nack := true;
      |end if;
    |$endif
  |$endif
  |$if blk_idx == blk_cnt - 1
    |r_multi := '0';
  |$endif
|$endblock
|
|$block AFTER_READ
  |@ Read logic for $desc$
  |$if phase == 'request'
    |if r_req then
    |$ AFTER_READ_RESP
    |end if;
  |$else
    |$AFTER_READ_RESP
  |$endif
  |$if blk_idx == 0 and read_tag is not None
    |$if phase == 'request'
      |if r_defer then
      |  r_dtag := $read_tag$;
      |end if;
    |$endif
  |$endif
|$endblock
|
|$block BEFORE_WRITE
  |$if phase == 'request'
    |@ Write logic for $desc$
    |if w_req or w_lreq then
    |  w_hold($bw*word_idx + bw-1$ downto $bw*word_idx$) := w_data;
    |  w_hstb($bw*word_idx + bw-1$ downto $bw*word_idx$) := w_strb;
    |  w_multi := '$'1' if blk_idx < blk_cnt - 1 else '0'$';
    |end if;
    |$if blk_idx < blk_cnt - 1
      |if w_req then
      |  w_ack := true;
      |end if;
    |$endif
  |$endif
|$endblock
|
|$block AFTER_WRITE
  |$if phase == 'request'
    |$if blk_idx == blk_cnt - 1 and write_tag is not None
      |if w_defer then
      |  w_dtag := $write_tag$;
      |end if;
    |$endif
  |$endif
|$endblock
|
|$if dir == 'r'
  |$if pos == 'before'
    |$BEFORE_READ
  |$else
    |$AFTER_READ
  |$endif
|$else
  |$if pos == 'before'
    |$BEFORE_WRITE
  |$else
    |$AFTER_WRITE
  |$endif
|$endif
""", comment='--')


_INTERNAL_SIGNAL_TEMPLATE = annotate_block("""
|$if s.is_strobe()
  |$s.use_name$ := $s.drive_name$;
  |$s.drive_name$ := $c$;
|$endif
|if reset = '1' then
|  $s.use_name$ := $c$;
|end if;
""", comment='--')


class VhdlEntityGenerator:
    """Generator for the entity and associated package for a single register
    file."""

    def __init__(self, regfile):
        """Constructs a VHDL generator for the given register file."""
        super().__init__()
        self._regfile = regfile

        # Main template engine, used to generate the actual VHDL files.
        self._tple = TemplateEngine()

        # Add some basic variables and shorthands to the template engine for
        # the template to use.
        self._tple['version'] = __version__
        self._tple['r'] = regfile
        self._tple['e'] = regfile.cfg.entity
        self._tple['bw'] = regfile.cfg.features.bus_width
        self._tple['ai'] = regfile.address_info
        self._tple['di'] = regfile.defer_tag_info
        self._tple['ii'] = regfile.interrupt_info

        # Interface builder.
        self._interface = Interface(regfile.name)

        # Construct address decoder builders.
        self._read_decoder = AddressDecoder(
            'r_addr', regfile.address_info.width,
            optimize=regfile.cfg.features.optimize,
            allow_duplicate=True, allow_overlap=True)
        self._write_decoder = AddressDecoder(
            'w_addr', regfile.address_info.width,
            optimize=regfile.cfg.features.optimize,
            allow_duplicate=True, allow_overlap=True)

        # Construct defer tag decoder builders.
        self._read_tag_decoder = AddressDecoder(
            'r_rtag', regfile.defer_tag_info.read_width,
            optimize=True, allow_duplicate=True)
        self._write_tag_decoder = AddressDecoder(
            'w_rtag', regfile.defer_tag_info.write_width,
            optimize=True, allow_duplicate=True)

        # Generate code for interrupts.
        for interrupt in regfile.interrupts:
            self._add_interrupt(interrupt)

        # Generate code for internal address concatenation.
        self._add_address_construction(
            regfile.address_info)

        # Generate code for subaddresses.
        self._add_subaddress_construction(
            regfile.iter_subaddresses())

        # Generate the block access code that comes before the field code.
        for register in regfile.registers:
            for address_block in register.blocks:
                self._add_address_block(address_block, 'before')

        # Generate code for fields.
        for field_descriptor in regfile.field_descriptors:
            BehaviorCodeGen.construct(
                field_descriptor,
                self._tple, self._interface,
                self._read_decoder, self._write_decoder,
                self._read_tag_decoder, self._write_tag_decoder).generate()

        # The fields share temporary variables for read/write/strobe data of
        # the right sizes for the fields, such that the templates don't have to
        # deal with those variables already representing VHDL slices. Generate
        # those shared variables here.
        tmp_variables = set()
        for field_descriptor in regfile.field_descriptors:
            size = field_descriptor.base_bitrange.shape
            if size is None:
                order = 0
                fmt = 'variable tmp_%s    : std_logic;'
            else:
                order = size
                fmt = 'variable tmp_%%s%-4d: std_logic_vector(%d downto 0);' % (
                    size, size - 1)
            tmp_variables.add((order, fmt % 'data'))
            if field_descriptor.behavior.bus.write is not None:
                tmp_variables.add((order, fmt % 'strb'))
        block = ['@ Temporary variables for the field templates.']
        block.extend((line for _, line in sorted(tmp_variables)))
        self._tple.append_block('DECLARATIONS', block)

        # Generate the block access code that comes after the field code.
        for register in regfile.registers:
            for address_block in register.blocks:
                self._add_address_block(address_block, 'after')

        # Add the address decoders to the main template engine.
        self._read_decoder.append_to_template(
            self._tple, 'FIELD_LOGIC_READ',
            'Read address decoder.')
        self._write_decoder.append_to_template(
            self._tple, 'FIELD_LOGIC_WRITE',
            'Write address decoder.')

        # Add the defer tag decoders to the main template engine.
        self._read_tag_decoder.append_to_template(
            self._tple, 'FIELD_LOGIC_READ_TAG',
            'Deferred read tag decoder.')
        self._write_tag_decoder.append_to_template(
            self._tple, 'FIELD_LOGIC_WRITE_TAG',
            'Deferred write tag decoder.')

        # Generate code for internal signals.
        for internal in regfile.internals:
            self._add_internal_signal(internal)
        for internal_io in regfile.internal_ios:
            self._add_internal_io_port(internal_io)

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

    @staticmethod
    def _describe_interrupt(interrupt):
        """Generates a description for an interrupt, to be used as block
        comment."""
        return '%s-sensitive interrupt %s: %s' % (
            'strobe' if interrupt.bus_can_clear else 'level',
            interrupt.name,
            interrupt.brief)

    @staticmethod
    def _describe_block(block):
        """Generates a description for a block, to be used as block comment."""
        return 'block %s: %s' % (
            block.name,
            block.brief)

    @staticmethod
    def _describe_internal(internal):
        """Generates a description for an internal signal, to be used as block
        comment."""
        return 'internal signal %s.' % (
            internal.name)

    @staticmethod
    def _describe_internal_io(internal_io):
        """Generates a description for an internal I/O port, to be used as
        block comment."""
        return '%s port for internal signal %s.' % (
            internal_io.direction,
            internal_io.internal.name)

    def _add_code_block(self, key, region, desc, block):
        """Adds a code block for the given key if the block is not `None`,
        prefixing a comment specifying what kind of block it is (`region`) and
        a description of the object that the block is for (`desc`)."""
        if block is not None:
            self._tple.append_block(key, '@ %s for %s' % (region, desc), block)

    def _add_interrupt(self, interrupt):
        """Adds the logic for asserting the internal interrupt request
        variable when an interrupt is requested."""
        desc = self._describe_interrupt(interrupt)

        # Get the name of the request input signal.
        if interrupt.is_internal():
            input_signal = interrupt.internal.use_name
        else:
            input_signal = self._interface.add(
                interrupt.name, desc, 'i', None,
                'request', 'i', None, interrupt.shape,
                interrupt.interface_options)

        # Construct template engine for the logic and populate variables.
        tple = TemplateEngine()
        tple['i'] = input_signal
        if interrupt.is_vector():
            tple['r'] = '%d downto %d' % (
                interrupt.offset + interrupt.width - 1, interrupt.offset)
        else:
            tple['r'] = '%d' % (interrupt.offset)
        tple['active'] = interrupt.active

        # Process the interrupt logic template and add it to the main template
        # engine.
        self._add_code_block(
            'IRQ_LOGIC', 'Logic', desc,
            tple.apply_str_to_str(_INTERRUPT_TEMPLATE, postprocess=False))

    def _add_address_construction(self, signals):
        """Adds the code for constructing the internal address to the template
        engine."""
        block = ['@ Concatenate page/condition signals to the address when '
                 'we\'re ready for a new command.']
        trivial = True
        for signal, offset in signals:
            if signal is AddressSignalMap.BUS:
                # This signal is always present, so it's part of the entity
                # template.
                continue
            trivial = False
            if signal.is_vector():
                block.append('{target}(%d downto %d) := %s;' % (
                    offset + signal.width - 1, offset, signal.use_name))
            else:
                block.append('{target}(%d) := %s;' % (
                    offset, signal.use_name))
        if trivial:
            return
        block = '\n'.join(block)
        self._tple.append_block('WRITE_ADDR_CONCAT', block.format(target='w_addr'))
        self._tple.append_block('READ_ADDR_CONCAT', block.format(target='r_addr'))

    @staticmethod
    def _bitrange_to_vhdl(bitrange):
        if bitrange.is_scalar():
            return '(%d)' % (bitrange.index,)
        return '(%d downto %d)' % (bitrange.high, bitrange.low)

    def _add_subaddress_construction(self, subaddresses):
        declarations = ['@ Subaddress variables, used to index within large '
                        'fields like memories and AXI passthroughs.']
        construct_read = ['@ Construct the subaddresses for read mode.']
        construct_write = ['@ Construct the subaddresses for write mode.']
        for subaddress in subaddresses:
            declarations.append(
                'variable %-20s : std_logic_vector(%d downto 0);'
                % (subaddress.name, subaddress.width - 1))

            for component in subaddress.components:
                if isinstance(component, SubAddress.BLANK):
                    if component.target.is_vector():
                        line = '%%s%%s := \"%s\";' % ('0' * component.target.width)
                    else:
                        line = '%s%s := \'0\';'
                    line %= subaddress.name, self._bitrange_to_vhdl(component.target)
                    construct_read.append(line)
                    construct_write.append(line)
                    continue

                if isinstance(component, SubAddress.ADDRESS):
                    line = '%s%s := %%s_addr%s;' % (
                        subaddress.name,
                        self._bitrange_to_vhdl(component.target),
                        self._bitrange_to_vhdl(component.source))
                    construct_read.append(line % 'r')
                    construct_write.append(line % 'w')
                    continue

                if isinstance(component, SubAddress.INTERNAL):
                    line = '%s%s := %s%s;' % (
                        subaddress.name,
                        self._bitrange_to_vhdl(component.target),
                        component.internal.use_name,
                        self._bitrange_to_vhdl(component.source))
                    construct_read.append(line)
                    construct_write.append(line)
                    continue

                assert False

            if subaddress.offset:
                line = '%s := std_logic_vector(unsigned(%s) + %d);' % (
                    subaddress.name, subaddress.name, subaddress.offset)
                construct_read.append(line)
                construct_write.append(line)

        if len(declarations) == 1:
            return

        self._tple.append_block('DECLARATIONS', declarations)
        self._tple.append_block('FIELD_LOGIC_READ', construct_read)
        self._tple.append_block('FIELD_LOGIC_WRITE', construct_write)

    def _add_address_block(self, address_block, position):
        """Adds the boilerplate bus logic for the given block. `position`
        indicates the relation of this function call with respect to the
        functions that add the field logic; if `'before'`, the function assumes
        that it is called before the field logic is added, if `'after'` it
        assumes after. Both variants must be called exactly once for each
        register."""
        tple = TemplateEngine()
        tple['pos'] = position
        tple['bw'] = self._regfile.cfg.features.bus_width
        tple['desc'] = self._describe_block(address_block)
        tple['blk_cnt'] = len(address_block.register.blocks)
        tple['blk_idx'] = address_block.index
        if address_block.register.endianness == 'little':
            tple['word_idx'] = address_block.index
        else:
            tple['word_idx'] = len(address_block.register.blocks) - address_block.index - 1
        tple['read_tag'] = address_block.read_tag
        tple['write_tag'] = address_block.write_tag
        if address_block.can_read():
            tple['dir'] = 'r'
            tple['phase'] = 'request'
            block = tple.apply_str_to_str(
                _BLOCK_ACCESS_TEMPLATE, postprocess=False)
            self._read_decoder[address_block.internal_address] = block
            if address_block.read_tag is not None:
                tple['phase'] = 'response'
                block = tple.apply_str_to_str(
                    _BLOCK_ACCESS_TEMPLATE, postprocess=False)
                self._read_tag_decoder[address_block.read_tag] = block
        if address_block.can_write():
            tple['dir'] = 'w'
            tple['phase'] = 'request'
            block = tple.apply_str_to_str(
                _BLOCK_ACCESS_TEMPLATE, postprocess=False)
            self._write_decoder[address_block.internal_address] = block
            if address_block.write_tag is not None:
                tple['phase'] = 'response'
                block = tple.apply_str_to_str(
                    _BLOCK_ACCESS_TEMPLATE, postprocess=False)
                self._write_tag_decoder[address_block.write_tag] = block

    def _add_internal_signal(self, internal):
        """Adds the boilerplate code that supports the given internal signal
        (such as its variable declaration) to the template engine."""
        desc = self._describe_internal(internal)

        # Determine signal type name and reset value.
        if internal.shape is None:
            clear = "'0'"
            typ = 'std_logic'
        else:
            clear = "(others => '0')"
            typ = 'std_logic_vector(%d downto 0)' % (internal.width - 1)

        # Variable declarations.
        block = 'variable %s : %s := %s;' % (internal.use_name, typ, clear)
        if internal.drive_name != internal.use_name:
            block += '\nvariable %s : %s := %s;' % (internal.drive_name, typ, clear)
        self._add_code_block('DECLARATIONS', 'Private declarations', desc, block)

        # Boilerplate logic.
        tple = TemplateEngine()
        tple['s'] = internal
        tple['c'] = clear
        block = tple.apply_str_to_str(
            _INTERNAL_SIGNAL_TEMPLATE, postprocess=False)
        self._add_code_block('INTERNAL_SIGNAL_LATE', 'Logic', desc, block)

    def _add_internal_io_port(self, internal_io):
        """Connects the given internal to a new I/O port."""
        desc = self._describe_internal_io(internal_io)
        mode = 'o' if internal_io.direction == 'output' else 'i'

        # Add the port.
        port = self._interface.add(
            internal_io.name, desc, 's', None,
            None, mode, None, internal_io.shape,
            internal_io.interface_options)

        # Connect the port to the internal signal.
        if internal_io.direction == 'input':
            key = 'INTERNAL_SIGNAL_EARLY'
            block = '%s := %s;' % (
                internal_io.internal.drive_name, port)
        elif internal_io.direction == 'strobe':
            key = 'INTERNAL_SIGNAL_EARLY'
            block = '%s := %s or %s;' % (
                internal_io.internal.drive_name, internal_io.internal.drive_name, port)
        else:
            assert internal_io.direction == 'output'
            key = 'INTERNAL_SIGNAL_LATE'
            block = '%s <= %s;' % (
                port, internal_io.internal.use_name)
        self._add_code_block(key, 'Logic', desc, block)

    def generate(self, output_dir, annotate=False):
        """Generates the files for this register file in the specified
        directory."""
        output_dir = os.path.normpath(output_dir)
        if '@' in output_dir:
            left, right = output_dir.split('@', maxsplit=1)

            relpath = ''
            if self._regfile.cfg.source_directory is not None:
                relpath = self._regfile.cfg.source_directory
                if relpath:
                    relpath = os.path.relpath(os.path.normpath(relpath))
            if relpath == '.':
                relpath = ''

            relpath = relpath.split(os.sep)

            output_dir = [left]
            if output_dir[-1].endswith(os.sep):
                output_dir.extend(relpath)
            else:
                output_dir[-1] += relpath[0]
                output_dir.extend(relpath[1:])
            if right.startswith(os.sep):
                output_dir.append(right[1:])
            else:
                output_dir[-1] += right

            output_dir = os.path.join(*output_dir)

            if output_dir == '.':
                output_dir = ''
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        name = os.path.join(output_dir, self._regfile.name)

        self._tple.apply_file_to_file(
            pjoin(_MODULE_DIR, 'entity.template.vhd'),
            name + '.gen.vhd',
            comment='-- ', annotate=annotate)
        print('Wrote %s.gen.vhd' % name)

        self._tple.apply_file_to_file(
            pjoin(_MODULE_DIR, 'package.template.vhd'),
            name + '_pkg.gen.vhd',
            comment='-- ', annotate=annotate)
        print('Wrote %s_pkg.gen.vhd' % name)

    def gather_ports(self):
        """Yields all the inputs/outputs/generics excluding `clk` and `reset`
        as `(mode, path, type, count)` four-tuples. `mode` is `'i'` for
        inputs, `'o'` for outputs, and `'g'` for generics. `count` is `None` if
        the type is not an incomplete array."""
        for mode, name, typ, count in self._interface.gather_ports():
            yield mode, name, typ, count
        yield 'i', 'bus_i', Axi4Lite('m2s', self._regfile.cfg.features.bus_width), None
        yield 'o', 'bus_o', Axi4Lite('s2m', self._regfile.cfg.features.bus_width), None


class VhdlEntitiesGenerator:
    """Generator for VHDL register file entities."""

    def __init__(self, regfiles):
        super().__init__()
        self._regfiles = regfiles

    def generate(self, output_dir, annotate=False):
        """Generates the HTML documentation files for the register files in the
        given directory."""
        for regfile in self._regfiles:
            VhdlEntityGenerator(regfile).generate(output_dir, annotate)


class VhdlPackageGenerator:
    """"Generator" for the VHDL package common to all of vhdmmio."""

    @staticmethod
    def generate(output_dir):
        """Generates the common `vhdmmio_pkg.gen.vhd` file in the given
        directory."""
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        tple = TemplateEngine()
        tple['version'] = __version__
        tple.apply_file_to_file(
            pjoin(_MODULE_DIR, 'vhdmmio_pkg.template.vhd'),
            pjoin(output_dir, 'vhdmmio_pkg.gen.vhd'),
            comment='-- ')
        print('Wrote %s' % pjoin(output_dir, 'vhdmmio_pkg.gen.vhd'))
