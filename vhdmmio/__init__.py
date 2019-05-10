"""vhdMMIO: AXI4-lite MMIO infrastructure generator"""

import sys
import re
import yaml

class RunComplete(Exception):
    """Exception used by `VhdMmio` to report that the program should terminate
    with the given exit code."""

    def __init__(self, code):
        super().__init__('Exit with code {}'.format(code))
        self.code = code


class RegisterFile:
    """Represents a register file description."""

    def __init__(self, name, brief=None, doc=None):
        """Constructs a new register file description.

         - `name` must be an identifier string that uniquely identifies the
           register file.
         - `brief` must either be `None` or a markdown string that serves as a
           one-line description of the register file.
         - `doc` must either be `None` or a markdown string that serves as more
           complete documentation of the register file.
        """
        super().__init__()

        self._name = str(name)
        if not re.match(r'[a-zA-Z][a-zA-Z_0-9]*', self._name):
            raise ValueError('name is not a valid identifier')

        self._brief = None
        self.brief = brief

        self._doc = None
        self.doc = doc

        self._yaml_source = None

    @property
    def name(self):
        """The name of the register file. Cannot be changed after
        construction."""
        return self._name

    @property
    def brief(self):
        """Brief, one-line markdown description of the register file."""
        return self._brief

    @brief.setter
    def brief(self, value):
        if value is None:
            self._brief = self._name
            return
        value = str(value)
        if re.search(r'\n[ \t]*\n', value):
            raise ValueError('brief must be a single line')
        self._brief = value

    @property
    def doc(self):
        """Multiline markdown documentation of the register file."""
        return self._brief

    @doc.setter
    def doc(self, value):
        if value is None:
            self._doc = ''
            return
        self._doc = str(value)

    @property
    def yaml_source(self):
        """The YAML file that this register file was loaded from, or `None` if
        it was constructed programmatically."""
        return self._yaml_source

    @classmethod
    def from_yaml(cls, filename):
        """Updates this `RegisterFile` object by loading the specified YAML
        description file into it."""
        with open(filename, 'r') as fil:
            data = yaml.load(fil.read())

        # Construct object.
        register_file = cls(
            name=data.pop('name'),
            brief=data.pop('brief', None),
            doc=data.pop('doc', None))

        # This function basically acts like a second constructor, so private
        # member access is fine here.
        register_file._yaml_source = filename #pylint: disable=W0212

        # Add fields.
        for field_data in data.pop('fields', []):
            raise NotImplementedError() # TODO

        # Guard against unexpected keys.
        if data:
            raise ValueError(
                'unexpected key(s) in register file description: {}'
                .format(list(data.keys())))

        return register_file

    def write_yaml(self, filename):
        """Writes the register file specification to a YAML file."""
        fields = [] # TODO

        data = {
            'name': self.name,
            'brief': self.brief,
            'doc': self.doc,
            'fields': fields,
        }

        with open(filename, 'w') as fil:
            fil.write(yaml.dump(data))

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
            self.add_register_file(RegisterFile.from_yaml(spec_file))

        # Generate the requested output files.
        self.generate()

    def parse_args(self, args):
        """Parse a list of command line arguments to configure this `VhdMmio`
        object. Returns the list of specification files that should be
        loaded."""
        raise NotImplementedError() # TODO

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
        raise NotImplementedError() # TODO


if __name__ == '__main__':
    try:
        VhdMmio().run()
    except RunComplete as exc:
        sys.exit(exc.code)
    # TODO: exception pretty-printing
