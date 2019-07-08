"""Submodule with a class that generates `Testbench`es for `RegisterFile`s."""

import functools
import tempfile
from vhdmmio.core.regfile import RegisterFile
from vhdmmio.vhdl import Generator, generate_pkg
from .main import Testbench
from .axi import AXI4LMasterMock, AXI4LSlaveMock

class AttributeDict:
    """Abstraction class for (nested) dictionaries that allows keys to be
    accessed as attributes and allows only read access."""

    def __init__(self, dictionary):
        super().__init__()
        self._dictionary = dictionary

    def __getitem__(self, key):
        data = self._dictionary[key]
        if isinstance(data, dict):
            return AttributeDict(data)
        return data

    def __getattr__(self, attr):
        try:
            return self[attr]
        except KeyError:
            raise AttributeError(str(attr))


class RegisterFileTestbench:
    """Testbench constructor and context manager for register files. Construct
    with a register file description, then use in a with `... as ...:`
    statement, where the returned object is an abstraction of all the testbench
    signal hooks and AXI ports on the register file interface. For instance,
    `.bus` returns the AXI master mock."""

    @staticmethod
    def _strip_suffix(suffix, name):
        if isinstance(name, str) and name.endswith('_%s' % suffix):
            return name[:-2]
        return name

    def __init__(self, data, *generics):
        """Constructs a testbench for a register file. `data` can be anything
        that `RegisterFile.load()` accepts."""
        super().__init__()
        self._regfile = RegisterFile.load(data)
        self._generator = Generator(self._regfile)
        self._testbench = Testbench()
        self._testbench.add_use('use work.%s_pkg.all;' % self._regfile.meta.name)
        self._tempdir = None

        decl = []
        inst = []
        conn = []
        inst.append('  uut: %s' % self._regfile.meta.name)
        if generics:
            inst.append('    generic map (')
            for name, value in generics[:-1]:
                inst.append('      %s => %s,' % (name, value))
            name, value = generics[-1]
            inst.append('      %s => %s' % (name, value))
            inst.append('    )')
        inst.append('    port map (')

        # Create testbench signal hooks/AXI4L mockups for all UUT ports.
        self._tb_obs = {}
        axi_mocks = {}
        for mode, name, typ, count in self._generator.gather_ports():

            # Skip generics.
            if mode == 'g':
                continue

            # Function that strips _<mode> tags from the end of names.
            strip_mode = functools.partial(self._strip_suffix, mode)

            # Add a signal for this port and connect it to the UUT.
            decl.append('%s;' % typ.make_signal('uut_%s' % name, count)[0])
            inst.append('      %s => uut_%s,' % (name, name))

            # Create testbench hooks for all the std_logic(_vector) members of
            # this port. Record any AXI4L signals we encounter to match them.
            for subpath, subtype, subcount in typ.gather_members(count):

                # Construct the VHDL reference for the uut_* signal.
                port_ref = ['uut_%s' % name]
                for ent in subpath:
                    if isinstance(ent, int):
                        port_ref.append('(%d)' % ent)
                    else:
                        port_ref.append('.%s' % ent)
                port_ref = ''.join(port_ref)

                # Handle primitives.
                if subtype.name in ('std_logic', 'std_logic_vector'):

                    # Construct a unique name for the testbench signal.
                    tb_ref = '_dot_'.join(['tb_%s' % name] + list(map(str, subpath)))

                    # Construct the testbench hook.
                    if mode == 'i':
                        tb_ob = self._testbench.add_input(tb_ref, subcount)
                        conn.append('%s <= %s;' % (port_ref, tb_ref))
                    else:
                        tb_ob = self._testbench.add_output(tb_ref, subcount)
                        conn.append('%s <= %s;' % (tb_ref, port_ref))

                    # Path to where the hook object is to be stored.
                    tb_path = [name] + subpath

                # Handle AXI.
                elif subtype.name.startswith('axi4l'):

                    # Get width and direction.
                    bus_width, is_cmd = {
                        'axi4l32_m2s': (32, True),
                        'axi4l64_m2s': (64, True),
                        'axi4l32_s2m': (32, False),
                        'axi4l64_s2m': (64, False),
                    }[subtype.name]

                    # Determine if we need to mock a bus master or slave.
                    if mode == 'i':
                        mock_master = is_cmd
                    else:
                        mock_master = not is_cmd

                    # Construct a unique name for the dictionary key.
                    tb_ref = ['tb_%s' % strip_mode(name)]
                    tb_ref.extend(map(str, map(strip_mode, subpath)))
                    tb_ref = '_dot_'.join(tb_ref)

                    # If we've not seen a signal for this bus before, record it
                    # in axi_mocks.
                    bus_data = axi_mocks.pop(tb_ref, None)
                    if bus_data is None:
                        axi_mocks[tb_ref] = {
                            'bus_width': bus_width,
                            'mock_master': mock_master,
                            'cmd' if is_cmd else 'resp': port_ref,
                        }
                        continue

                    # Assert that this signal together with the one we've
                    # found earlier makes for a consistent AXI bus.
                    assert bus_data['bus_width'] == bus_width
                    assert bus_data['mock_master'] == mock_master
                    assert 'cmd' if is_cmd else 'resp' not in bus_data
                    assert 'resp' if is_cmd else 'cmd' in bus_data
                    bus_data['cmd' if is_cmd else 'resp'] = port_ref

                    # Construct the mockup.
                    if mock_master:
                        tb_ob = AXI4LMasterMock(self._testbench, tb_ref, bus_width)
                        conn.append('%s <= %s_req;' % (bus_data['cmd'], tb_ref))
                        conn.append('%s_resp <= %s;' % (tb_ref, bus_data['resp']))
                    else:
                        tb_ob = AXI4LSlaveMock(self._testbench, tb_ref, bus_width)
                        conn.append('%s_req <= %s;' % (tb_ref, bus_data['cmd']))
                        conn.append('%s <= %s_resp;' % (bus_data['resp'], tb_ref))

                    # Construct the path that the user will use to access the
                    # mockup unit. This is the same path style used for regular
                    # signals, but with all _i/_o suffixes stripped.
                    tb_path = [strip_mode(name)]
                    tb_path.extend(map(strip_mode, subpath))

                else:

                    # Unsupported primitive type.
                    raise NotImplementedError(
                        'unsupported primitive type for port: %s' % subtype.name)

                # Save the testbench hook in the right place.
                sub = self._tb_obs
                for ent in tb_path[:-1]:
                    if ent not in sub:
                        sub[ent] = {}
                    sub = sub[ent]
                sub[tb_path[-1]] = tb_ob

        if axi_mocks:
            raise ValueError(
                'failed to match all AXI4L ports, remaining identifiers: %s'
                % ', '.join(axi_mocks))

        inst.append('      clk => clk,')
        inst.append('      reset => reset')
        inst.append('    );')

        self._testbench.add_head('\n'.join(decl))
        self._testbench.add_body('\n'.join(inst))
        self._testbench.add_body('\n'.join(conn))

    def __enter__(self):
        self._tempdir = tempfile.TemporaryDirectory()
        self._generator.generate_files(self._tempdir.name)
        generate_pkg(self._tempdir.name)
        self._testbench.add_include(self._tempdir.name)
        self._testbench.__enter__()
        self._testbench.reset()
        return AttributeDict(self._tb_obs)

    def __exit__(self, *args):
        self._testbench.__exit__(*args)
        if self._tempdir is not None:
            self._tempdir.cleanup()
            self._tempdir = None

    @property
    def regfile(self):
        """Returns the `RegisterFile` object."""
        return self._regfile

    @property
    def generator(self):
        """Returns the `Generator` object."""
        return self._generator

    @property
    def testbench(self):
        """Returns the `Testbench` object."""
        return self._testbench

    @property
    def tempdir(self):
        """Returns the temporary directory that the VHDL files for the register
        file are generated in. Only valid when inside the context."""
        if self._tempdir is None:
            return None
        return self._tempdir.name
