# Copyright 2018 Delft University of Technology
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Main module for vhdmmio.

Use `run_cli()` to run vhdmmio as if it was run from the command line. For a
more script-friendly interface, use `RegisterFile.load()`, `generate_html()`,
and `generate_vhdl()`."""

import sys
import os
import argparse
from .core.regfile import RegisterFile
from .html import generate as generate_html
from .vhdl import generate as generate_vhdl

__version__ = '0.0.1'

def run_cli(args=None):
    """Runs the vhdmmio CLI. The command-line arguments are taken from `args`
    when specified, or `sys.argv` by default. The return value is the exit code
    for the process. All exceptions are caught by default; to suppress this
    behavior pass `--stacktrace`."""

    # Construct the main argument parser.
    parser = argparse.ArgumentParser(
        description='This script generates AXI4L-compatible register files '
        'from simple YAML or JSON descriptions.')

    parser.add_argument(
        '-i', '--input',
        action='append',
        help='Specifies an input file or input directory. Input files with '
        'a .json file extension are parsed as JSON files, otherwise YAML is '
        'assumed. YAML is recommended for writing register file descriptions '
        'manually, but JSON is more universally supported in case you want to '
        'generate the description with some other tool. If the specified path '
        'is a directory, it is searched recursively for *.mmio.yaml and '
        '*.mmio.json files. You can specifify this argument multiple times '
        'to specify multiple input files. If you don\'t specify it at all, '
        'the current working directory is searched recursively.')

    parser.add_argument(
        '-o', '--output', default=None,
        help='Output directory. If not specified, files that belong to a '
        'register file are written to the directory that contains its '
        'description file, and files that do not are written to the current '
        'working directory.')

    parser.add_argument(
        '--stacktrace', action='store_true',
        help='Print complete Python stack traces instead of just the message.')

    parser.add_argument(
        '-v', '--version', action='version', version='vhdmmio ' + __version__,
        help='Prints the current version of vhdeps and exits.')

    generators = parser.add_subparsers(
        title='generators',
        dest='generator')

    # Construct the argument subparser for the pkg generator.
    _ = generators.add_parser(
        'pkg', help='Writes the VHDL support package.',
        description='Writes the vhdmmio_pkg.vhd support package, needed once for '
        'each project.')

    # Construct the argument subparser for the vhdl generator.
    vhdl_generator_parser = generators.add_parser(
        'vhdl', help='Generates VHDL sources.',
        description='Generates VHDL code for the given register file '
        'descriptions. Two files are generated per register file: a package '
        'containing the component declaration and type definitions for the '
        'interface, and the entity/architecture itself. They are named based '
        'on the name of the register file, so make sure this is unique within '
        'your project.')

    vhdl_generator_parser.add_argument(
        '--annotate', action='store_true',
        help='Annotates the generated VHDL files with template file and line '
        'number information for debugging vhdmmio.')

    # Construct the argument subparser for the html generator.
    _ = generators.add_parser(
        'html', help='Generates HTML documentation.',
        description='Generates HTML documentation for the given register file '
        'descriptions.')

    try:

        # Parse the command line.
        if args is None:
            args = sys.argv[1:]
        args = parser.parse_args(args)

        # Make sure that a generator was specified.
        if args.generator is None:
            print('Error: no generator specified.', file=sys.stderr)
            parser.print_usage()
            return 1

    except SystemExit as exc:
        return exc.code

    try:

        # Handle the pkg generator before loading any register file
        # descriptions.
        if args.generator == 'pkg':

            # Read the support package.
            fname = os.path.dirname(__file__) + os.sep + 'vhdl' + os.sep + 'vhdmmio_pkg.vhd'
            with open(fname, 'r') as fil:
                data = fil.read()

            # Write the support package.
            output_directory = '.'
            if args.output is not None:
                output_directory = args.output
            fname = output_directory + os.sep + 'vhdmmio_pkg.vhd'
            with open(fname, 'w') as fil:
                fil.write(data)

            print('Wrote %s' % fname)
            return 0

        # Look for input files.
        input_paths = args.input
        if not input_paths:
            print(
                'Note: recursively searching for register file descriptions '
                'in the working directory by default')
            input_paths = ['.']

        input_files = []
        for input_path in input_paths:
            if os.path.isfile(input_path):
                input_files.append(input_path)
            elif not os.path.isdir(input_path):
                continue
            for root, _, files in os.walk(input_path):
                for name in files:
                    if name.endswith('.mmio.yaml') or name.endswith('.mmio.json'):
                        input_files.append(os.path.join(root, name))

        if not input_files:
            print('No input files found!')
            return 1

        # Load the input files.
        register_files = []
        for input_file in input_files:
            register_files.append(RegisterFile.load(input_file))

        # Handle the VHDL generator.
        if args.generator == 'vhdl':
            generate_vhdl(register_files, args.output, args.annotate)

        # Handle the HTML generator.
        if args.generator == 'html':
            generate_html(register_files, args.output)

        return 0

    except Exception as exc: #pylint: disable=W0703
        if args.stacktrace:
            raise
        print('%s: %s' % (str(type(exc).__name__), str(exc)), file=sys.stderr)
        return 1

    except KeyboardInterrupt as exc:
        if args.stacktrace:
            raise
        return 1

def _init():
    if __name__ == '__main__':
        sys.exit(run_cli())

_init()
