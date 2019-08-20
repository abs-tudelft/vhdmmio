"""Module for generating VHDL for the register files."""

import os
from os.path import join as pjoin
import shutil
from ..template import TemplateEngine, annotate_block
from .types import Axi4Lite, gather_defs
from .interface import Interface

_MODULE_DIR = os.path.dirname(__file__)


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
        self._tple['r'] = regfile
        self._tple['bw'] = regfile.cfg.features.bus_width
        self._tple['dt'] = regfile.defer_tag_info
        self._tple['ii'] = regfile.interrupt_info

        # Interface builder.
        self._interface = Interface(regfile.name)

        # Address decoder builders.
        #self._read_decoder = AddressDecoder('r_addr', 32, optimize=regfile.optimize)
        #self._read_tag_decoder = AddressDecoder('r_rtag', regfile.read_tag_width, optimize=True)
        #self._write_decoder = AddressDecoder('w_addr', 32, optimize=regfile.optimize)
        #self._write_tag_decoder = AddressDecoder('w_rtag', regfile.write_tag_width, optimize=True)

        # Generate code for interrupts.
        #for interrupt in regfile.interrupts:
            #interrupt.generate_vhdl(self)

        # Generate boilerplate register access code before field code.
        #for register in regfile.registers:
            #self._add_register_boilerplate(register, 'before')

        # Generate code for fields.
        #for field_descriptor in regfile.field_descriptors:
            #field_descriptor.logic.generate_vhdl(self)

        # Generate boilerplate register access code after field code.
        #for register in regfile.registers:
            #self._add_register_boilerplate(register, 'after')

        # Add the decoders to the main template engine.
        #self._read_decoder.append_to_template(
            #self._tple, 'FIELD_LOGIC_READ',
            #'Read address decoder.')
        #self._read_tag_decoder.append_to_template(
            #self._tple, 'FIELD_LOGIC_READ_TAG',
            #'Deferred read tag decoder.')
        #self._write_decoder.append_to_template(
            #self._tple, 'FIELD_LOGIC_WRITE',
            #'Write address decoder.')
        #self._write_tag_decoder.append_to_template(
            #self._tple, 'FIELD_LOGIC_WRITE_TAG',
            #'Deferred write tag decoder.')

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
        #for internal_signal in regfile.internal_signals:
            #self._add_internal_signal_boilerplate(internal_signal)

    def generate(self, output_dir, annotate=False):
        """Generates the files for this register file in the specified
        directory."""
        relpath = ''
        if self._regfile.cfg.source_directory is not None:
            relpath = os.path.relpath(self._regfile.cfg.source_directory)
        output_dir = output_dir.replace('@', relpath)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        name = output_dir + os.sep + self._regfile.name

        self._tple.apply_file_to_file(
            pjoin(_MODULE_DIR, 'entity.template.vhd'),
            name + '.gen.vhd',
            comment='-- ', annotate=annotate)
        print('Wrote %s.vhd' % name)

        self._tple.apply_file_to_file(
            pjoin(_MODULE_DIR, 'package.template.vhd'),
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
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        for regfile in self._regfiles:
            VhdlEntityGenerator(regfile).generate(output_dir, annotate)


class VhdlPackageGenerator:
    """"Generator" for the VHDL package common to all of vhdmmio."""

    @staticmethod
    def generate(output_dir):
        """Generates the HTML documentation files for the register files in the
        given directory."""
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        shutil.copyfile(
            pjoin(_MODULE_DIR, 'vhdmmio_pkg.vhd'),
            pjoin(output_dir, 'vhdmmio_pkg.gen.vhd'))
