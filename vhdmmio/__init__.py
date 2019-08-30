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

Use `run_cli()` to run vhdmmio as if it was run from the command line."""

import sys
import os
import argparse
from vhdmmio.version import __version__
from vhdmmio.vhdl import VhdlEntitiesGenerator, VhdlPackageGenerator
from vhdmmio.html import HtmlDocumentationGenerator
from vhdmmio.config import RegisterFileConfig
from vhdmmio.core import RegisterFile

def run_cli(args=None):
    """Runs the vhdmmio CLI. The command-line arguments are taken from `args`
    when specified, or `sys.argv` by default. The return value is the exit code
    for the process. All exceptions are caught by default; to suppress this
    behavior pass `--stacktrace`."""

    parser = argparse.ArgumentParser(
        description='This script generates AXI4L-compatible register files '
        'from simple YAML or JSON descriptions. Visit '
        'https://github.com/abs-tudelft/vhdmmio for more information.')

    parser.add_argument(
        'source', nargs='*',
        help='Register description source files. You can either specify '
        'description files directly, or specify directories to be searched '
        'recursively. When searching, vhdmmio will match \'*.mmio.yaml\' '
        'and \'*.mmio.json\'.')

    parser.add_argument(
        '-P', '--pkg', metavar='dir', const='.', nargs='?',
        help='Write the \'vhdmmio_pkg.gen.vhd\' support package to the given '
        'directory. The directory defaults to the current working directory. '
        'You should only ever have to do this once, or maybe after you update '
        'vhdmmio; it does not depend on the register file descriptions.')

    parser.add_argument(
        '-V', '--vhd', metavar='dir', const='@', nargs='?',
        help='Generate VHDL files. If [dir] is specified, it is used as the '
        'output directory. You can use the \'@\' symbol to have vhdmmio '
        'insert the relative path from the current working directory to the '
        'register file description into the path. The directory defaults to '
        'just \'@\', so generated files are placed next to their YAML '
        'description by default.')

    parser.add_argument(
        '-H', '--html', metavar='dir', const='vhdmmio-doc', nargs='?',
        help='Generate HTML documentation for the register files. [dir] '
        'defaults to \'./vhdmmio-doc\'.')

    parser.add_argument(
        '--trusted', action='store_true',
        help='Indicates that the register description source files come from '
        'a trusted source. This allows the "custom" field behavior to be '
        'used, which, through vhdmmio\'s template engine, can potentially '
        'execute arbitrary Python code.')

    parser.add_argument(
        '--vhd-annotate', action='store_true',
        help='Annotate VHDL files with template line number information. You '
        'would only do this when you need to debug vhdmmio itself.')

    parser.add_argument(
        '--stacktrace', action='store_true',
        help='Print complete Python stack traces instead of just the message.')

    parser.add_argument(
        '-v', '--version', action='version', version='vhdmmio ' + __version__,
        help='Prints the current version of vhdmmio and exits.')

    try:
        if args is None:
            args = sys.argv[1:]
        args = parser.parse_args(args)

        if not args.source:
            args.source = ['.']

    except SystemExit as exc:
        return exc.code

    try:

        # Look for input files.
        input_files = []
        for input_path in args.source:
            if os.path.isfile(input_path):
                input_files.append(input_path)
            elif not os.path.isdir(input_path):
                print('Error: could not find input file/directory %s' % input_path)
                return 1
            for root, _, files in os.walk(input_path):
                for name in files:
                    if name.endswith('.mmio.yaml') or name.endswith('.mmio.json'):
                        input_files.append(os.path.join(root, name))

        # Load the input files.
        register_files_cfgs = list(map(RegisterFileConfig.load, input_files))

        # Compile the register files.
        register_files = [
            RegisterFile(cfg, trusted=args.trusted)
            for cfg in register_files_cfgs]

        # Print that the front-end is complete.
        if not register_files:
            print('Warning: no register files found!')
        elif len(register_files) == 1:
            print('Loaded 1 register file')
        else:
            print('Loaded %d register files' % len(register_files))

        # Handle the VHDL package generator.
        if args.pkg is not None:
            gen = VhdlPackageGenerator()
            gen.generate(args.pkg)

        # Handle the VHDL register file generator.
        if args.vhd is not None:
            gen = VhdlEntitiesGenerator(register_files)
            gen.generate(args.vhd, annotate=args.vhd_annotate)

        # Handle the HTML documentation generator.
        if args.html:
            gen = HtmlDocumentationGenerator(register_files)
            gen.generate(args.html)

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
