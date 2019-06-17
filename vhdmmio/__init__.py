"""vhdMMIO: AXI4-lite MMIO infrastructure generator"""

import sys
import re
from enum import Enum
import yaml
from .core.regfile import RegisterFile
from .html import HtmlGenerator
from .vhdl import VhdlGenerator

class RunComplete(Exception):
    """Exception used by `VhdMmio` to report that the program should terminate
    with the given exit code."""

    def __init__(self, code):
        super().__init__('Exit with code {}'.format(code))
        self.code = code

class VhdMmio:
    """Main class for vhdMMIO, representing a single run."""

    def __init__(self):
        super().__init__()
        self.register_files = []

    def run(self, args=None):
        """Runs vhdMMIO as if it were called from the command line.

        A custom command-line argument list can be passed to the `args` keyword
        argument. If this is not done, the list is taken from `sys.argv`.

        When something exceptional happens, this function raises the exception
        instead of printing it."""

        # Take arguments from sys.argv if the user did not override them.
        if args is None:
            args = sys.argv

        # Parse the command-line arguments.
        spec_files = self.parse_args(args)

        # Load/parse the register file descriptions.
        for spec_file in spec_files:
            with open(spec_file, 'r') as fil:
                spec = fil.read()
            if hasattr(yaml, 'safe_load'):
                spec = yaml.safe_load(spec)
            else:
                spec = yaml.load(spec)
            self.add_register_file(RegisterFile.from_dict(spec))

        # Generate the requested output files.
        self.generate()

    def parse_args(self, args):
        """Parse a list of command line arguments to configure this `VhdMmio`
        object. Returns the list of specification files that should be
        loaded."""
        return args[1:]

    def add_register_file(self, register_file):
        """Adds a `RegisterFile` object to the list of register files that are
        to be generated in this run."""
        if not isinstance(register_file, RegisterFile):
            raise TypeError(
                'Expected an object of type RegisterFile, received {}'
                .format(type(RegisterFile)))
        self.register_files.append(register_file)

    def generate(self):
        """Produces the output files requested by the previously loaded
        configuration using the previously loaded specification files."""
        VhdlGenerator(self.register_files, 'temp/output')
        HtmlGenerator(self.register_files, 'temp/output')
