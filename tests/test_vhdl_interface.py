"""Unit tests for the VHDL entity interface generator."""

from unittest import TestCase
import vhdmmio.vhdl.types as types
from vhdmmio.vhdl.interface import Interface
from vhdmmio.config import InterfaceConfig
from vhdmmio.core import InterfaceOptions

class TestVhdlInterface(TestCase):
    """Unit tests for the VHDL entity interface generator."""

    maxDiff = None

    @staticmethod
    def gen_basic_interface(group, flatten):
        """Generates a simple interface with the given grouping and
        flattening."""
        options = InterfaceOptions(InterfaceConfig(
            group=group, flatten=flatten,
            generic_group=group, generic_flatten=flatten))
        iface = Interface('tns')

        objs = [iface]

        objs.append(iface.add(
            'foo', 'field foo: a scalar field.', 'f', None,
            'data', 'i', types.std_logic_vector, 8, options))
        objs.append(iface.add(
            'foo', 'field foo: a scalar field.', 'f', None,
            'valid', 'i', types.std_logic, None, options))
        objs.append(iface.add(
            'foo', 'field foo: a scalar field.', 'f', None,
            'ready', 'o', types.std_logic, None, options))
        objs.append(iface.add(
            'foo', 'field foo: a scalar field.', 'f', None,
            'enable', 'g', types.boolean, None, options))

        objs.append(iface.add(
            'bar', 'field bar: a vector field.', 'f', 4,
            'data', 'o', types.std_logic_vector, 8, options))
        objs.append(iface.add(
            'bar', 'field bar: a vector field.', 'f', 4,
            'valid', 'o', types.std_logic, None, options))
        objs.append(iface.add(
            'bar', 'field bar: a vector field.', 'f', 4,
            'ready', 'i', types.std_logic, None, options))
        objs.append(iface.add(
            'bar', 'field bar: a vector field.', 'f', 4,
            'enable', 'g', types.boolean, None, options))

        return tuple(objs)

    def test_ungrouped_unflattened(self):
        """test ungrouped, unflattened interface generation"""
        result = self.gen_basic_interface(False, False)
        iface, foo_d, foo_v, foo_r, foo_e, bar_d, bar_v, bar_r, bar_e = result
        self.assertEqual('\n\n'.join(iface.generate('port')), '\n'.join([
            '@ Interface for field foo: a scalar field.',
            'f_foo_i : in tns_f_foo_i_type@:= TNS_F_FOO_I_RESET;',
            'f_foo_o : out tns_f_foo_o_type@:= TNS_F_FOO_O_RESET;',
            '',
            '@ Interface for field bar: a vector field.',
            'f_bar_o : out tns_f_bar_o_array(0 to 3)@:= (others => TNS_F_BAR_O_RESET);',
            'f_bar_i : in tns_f_bar_i_array(0 to 3)@:= (others => TNS_F_BAR_I_RESET);',
        ]))
        result = iface.generate('generic', end_with_semicolon=False)
        self.assertEqual('\n\n'.join(result), '\n'.join([
            '@ Interface for field foo: a scalar field.',
            'F_FOO_G : tns_f_foo_g_type@:= TNS_F_FOO_G_RESET;',
            '',
            '@ Interface for field bar: a vector field.',
            'F_BAR_G : tns_f_bar_g_array(0 to 3)@:= (others => TNS_F_BAR_G_RESET)',
        ]))
        self.assertEqual('\n'.join(types.gather_defs(*iface.gather_types())), '\n'.join([
            'type tns_f_foo_i_type is record',
            '  data : std_logic_vector(7 downto 0);',
            '  valid : std_logic;',
            'end record;',
            'constant TNS_F_FOO_I_RESET : tns_f_foo_i_type := (',
            '  data => (others => \'0\'),',
            '  valid => \'0\'',
            ');',
            'type tns_f_foo_o_type is record',
            '  ready : std_logic;',
            'end record;',
            'constant TNS_F_FOO_O_RESET : tns_f_foo_o_type := (',
            '  ready => \'0\'',
            ');',
            'type tns_f_foo_g_type is record',
            '  enable : boolean;',
            'end record;',
            'constant TNS_F_FOO_G_RESET : tns_f_foo_g_type := (',
            '  enable => false',
            ');',
            'type tns_f_bar_o_type is record',
            '  data : std_logic_vector(7 downto 0);',
            '  valid : std_logic;',
            'end record;',
            'constant TNS_F_BAR_O_RESET : tns_f_bar_o_type := (',
            '  data => (others => \'0\'),',
            '  valid => \'0\'',
            ');',
            'type tns_f_bar_o_array is array (natural range <>) of tns_f_bar_o_type;',
            'type tns_f_bar_i_type is record',
            '  ready : std_logic;',
            'end record;',
            'constant TNS_F_BAR_I_RESET : tns_f_bar_i_type := (',
            '  ready => \'0\'',
            ');',
            'type tns_f_bar_i_array is array (natural range <>) of tns_f_bar_i_type;',
            'type tns_f_bar_g_type is record',
            '  enable : boolean;',
            'end record;',
            'constant TNS_F_BAR_G_RESET : tns_f_bar_g_type := (',
            '  enable => false',
            ');',
            'type tns_f_bar_g_array is array (natural range <>) of tns_f_bar_g_type;',
        ]))
        self.assertEqual(str(foo_d['a']['b']), 'f_foo_i.data(b)')
        self.assertEqual(str(foo_v['a']['b']), 'f_foo_i.valid')
        self.assertEqual(str(foo_r['a']['b']), 'f_foo_o.ready')
        self.assertEqual(str(foo_e['a']['b']), 'F_FOO_G.enable')
        self.assertEqual(str(bar_d['a']['b']), 'f_bar_o(a).data(b)')
        self.assertEqual(str(bar_v['a']['b']), 'f_bar_o(a).valid')
        self.assertEqual(str(bar_r['a']['b']), 'f_bar_i(a).ready')
        self.assertEqual(str(bar_e['a']['b']), 'F_BAR_G(a).enable')

    def test_grouped_unflattened(self):
        """test grouped, unflattened interface generation"""
        result = self.gen_basic_interface('test', False)
        iface, foo_d, foo_v, foo_r, foo_e, bar_d, bar_v, bar_r, bar_e = result
        self.assertEqual('\n\n'.join(iface.generate('port')), '\n'.join([
            '@ Interface group for:',
            '@  - field bar: a vector field.',
            '@  - field foo: a scalar field.',
            'g_test_i : in tns_g_test_i_type@:= TNS_G_TEST_I_RESET;',
            'g_test_o : out tns_g_test_o_type@:= TNS_G_TEST_O_RESET;',
        ]))
        result = iface.generate('generic', end_with_semicolon=False)
        self.assertEqual('\n\n'.join(result), '\n'.join([
            '@ Interface group for:',
            '@  - field bar: a vector field.',
            '@  - field foo: a scalar field.',
            'G_TEST_G : tns_g_test_g_type@:= TNS_G_TEST_G_RESET',
        ]))
        self.assertEqual('\n'.join(types.gather_defs(*iface.gather_types())), '\n'.join([
            'type tns_f_foo_i_type is record',
            '  data : std_logic_vector(7 downto 0);',
            '  valid : std_logic;',
            'end record;',
            'constant TNS_F_FOO_I_RESET : tns_f_foo_i_type := (',
            '  data => (others => \'0\'),',
            '  valid => \'0\'',
            ');',
            'type tns_f_bar_i_type is record',
            '  ready : std_logic;',
            'end record;',
            'constant TNS_F_BAR_I_RESET : tns_f_bar_i_type := (',
            '  ready => \'0\'',
            ');',
            'type tns_f_bar_i_array is array (natural range <>) of tns_f_bar_i_type;',
            'type tns_g_test_i_type is record',
            '  f_foo : tns_f_foo_i_type;',
            '  f_bar : tns_f_bar_i_array(0 to 3);',
            'end record;',
            'constant TNS_G_TEST_I_RESET : tns_g_test_i_type := (',
            '  f_foo => TNS_F_FOO_I_RESET,',
            '  f_bar => (others => TNS_F_BAR_I_RESET)',
            ');',
            'type tns_f_foo_o_type is record',
            '  ready : std_logic;',
            'end record;',
            'constant TNS_F_FOO_O_RESET : tns_f_foo_o_type := (',
            '  ready => \'0\'',
            ');',
            'type tns_f_bar_o_type is record',
            '  data : std_logic_vector(7 downto 0);',
            '  valid : std_logic;',
            'end record;',
            'constant TNS_F_BAR_O_RESET : tns_f_bar_o_type := (',
            '  data => (others => \'0\'),',
            '  valid => \'0\'',
            ');',
            'type tns_f_bar_o_array is array (natural range <>) of tns_f_bar_o_type;',
            'type tns_g_test_o_type is record',
            '  f_foo : tns_f_foo_o_type;',
            '  f_bar : tns_f_bar_o_array(0 to 3);',
            'end record;',
            'constant TNS_G_TEST_O_RESET : tns_g_test_o_type := (',
            '  f_foo => TNS_F_FOO_O_RESET,',
            '  f_bar => (others => TNS_F_BAR_O_RESET)',
            ');',
            'type tns_f_foo_g_type is record',
            '  enable : boolean;',
            'end record;',
            'constant TNS_F_FOO_G_RESET : tns_f_foo_g_type := (',
            '  enable => false',
            ');',
            'type tns_f_bar_g_type is record',
            '  enable : boolean;',
            'end record;',
            'constant TNS_F_BAR_G_RESET : tns_f_bar_g_type := (',
            '  enable => false',
            ');',
            'type tns_f_bar_g_array is array (natural range <>) of tns_f_bar_g_type;',
            'type tns_g_test_g_type is record',
            '  f_foo : tns_f_foo_g_type;',
            '  f_bar : tns_f_bar_g_array(0 to 3);',
            'end record;',
            'constant TNS_G_TEST_G_RESET : tns_g_test_g_type := (',
            '  f_foo => TNS_F_FOO_G_RESET,',
            '  f_bar => (others => TNS_F_BAR_G_RESET)',
            ');',
        ]))
        self.assertEqual(str(foo_d['a']['b']), 'g_test_i.f_foo.data(b)')
        self.assertEqual(str(foo_v['a']['b']), 'g_test_i.f_foo.valid')
        self.assertEqual(str(foo_r['a']['b']), 'g_test_o.f_foo.ready')
        self.assertEqual(str(foo_e['a']['b']), 'G_TEST_G.f_foo.enable')
        self.assertEqual(str(bar_d['a']['b']), 'g_test_o.f_bar(a).data(b)')
        self.assertEqual(str(bar_v['a']['b']), 'g_test_o.f_bar(a).valid')
        self.assertEqual(str(bar_r['a']['b']), 'g_test_i.f_bar(a).ready')
        self.assertEqual(str(bar_e['a']['b']), 'G_TEST_G.f_bar(a).enable')

    def test_ungrouped_flattened_records(self):
        """test ungrouped, record-flattened interface generation"""
        result = self.gen_basic_interface(False, 'record')
        iface, foo_d, foo_v, foo_r, foo_e, bar_d, bar_v, bar_r, bar_e = result
        self.assertEqual('\n\n'.join(iface.generate('port')), '\n'.join([
            '@ Interface for field foo: a scalar field.',
            'f_foo_data : in std_logic_vector(7 downto 0)@:= (others => \'0\');',
            'f_foo_valid : in std_logic@:= \'0\';',
            'f_foo_ready : out std_logic@:= \'0\';',
            '',
            '@ Interface for field bar: a vector field.',
            'f_bar_data : out tns_f_bar_data_array(0 to 3)@:= (others => (others => \'0\'));',
            'f_bar_valid : out std_logic_array(0 to 3)@:= (others => \'0\');',
            'f_bar_ready : in std_logic_array(0 to 3)@:= (others => \'0\');',
        ]))
        result = iface.generate('generic', end_with_semicolon=False)
        self.assertEqual('\n\n'.join(result), '\n'.join([
            '@ Interface for field foo: a scalar field.',
            'F_FOO_ENABLE : boolean@:= false;',
            '',
            '@ Interface for field bar: a vector field.',
            'F_BAR_ENABLE : boolean_array(0 to 3)@:= (others => false)',
        ]))
        self.assertEqual('\n'.join(types.gather_defs(*iface.gather_types())), '\n'.join([
            'subtype tns_f_bar_data_type is std_logic_vector(7 downto 0);',
            'type tns_f_bar_data_array is array (natural range <>) of tns_f_bar_data_type;',
        ]))
        self.assertEqual(str(foo_d['a']['b']), 'f_foo_data(b)')
        self.assertEqual(str(foo_v['a']['b']), 'f_foo_valid')
        self.assertEqual(str(foo_r['a']['b']), 'f_foo_ready')
        self.assertEqual(str(foo_e['a']['b']), 'F_FOO_ENABLE')
        self.assertEqual(str(bar_d['a']['b']), 'f_bar_data(a)(b)')
        self.assertEqual(str(bar_v['a']['b']), 'f_bar_valid(a)')
        self.assertEqual(str(bar_r['a']['b']), 'f_bar_ready(a)')
        self.assertEqual(str(bar_e['a']['b']), 'F_BAR_ENABLE(a)')

    def test_grouped_flattened_records(self):
        """test grouped, record-flattened interface generation"""
        result = self.gen_basic_interface('test', 'record')
        iface, foo_d, foo_v, foo_r, foo_e, bar_d, bar_v, bar_r, bar_e = result
        self.assertEqual('\n\n'.join(iface.generate('port')), '\n'.join([
            '@ Interface group for:',
            '@  - field bar: a vector field.',
            '@  - field foo: a scalar field.',
            'g_test_i : in tns_g_test_i_type@:= TNS_G_TEST_I_RESET;',
            'g_test_o : out tns_g_test_o_type@:= TNS_G_TEST_O_RESET;',
        ]))
        result = iface.generate('generic', end_with_semicolon=False)
        self.assertEqual('\n\n'.join(result), '\n'.join([
            '@ Interface group for:',
            '@  - field bar: a vector field.',
            '@  - field foo: a scalar field.',
            'G_TEST_G : tns_g_test_g_type@:= TNS_G_TEST_G_RESET',
        ]))
        self.assertEqual('\n'.join(types.gather_defs(*iface.gather_types())), '\n'.join([
            'type tns_g_test_i_type is record',
            '  f_foo_data : std_logic_vector(7 downto 0);',
            '  f_foo_valid : std_logic;',
            '  f_bar_ready : std_logic_array(0 to 3);',
            'end record;',
            'constant TNS_G_TEST_I_RESET : tns_g_test_i_type := (',
            '  f_foo_data => (others => \'0\'),',
            '  f_foo_valid => \'0\',',
            '  f_bar_ready => (others => \'0\')',
            ');',
            'subtype tns_f_bar_data_type is std_logic_vector(7 downto 0);',
            'type tns_f_bar_data_array is array (natural range <>) of tns_f_bar_data_type;',
            'type tns_g_test_o_type is record',
            '  f_foo_ready : std_logic;',
            '  f_bar_data : tns_f_bar_data_array(0 to 3);',
            '  f_bar_valid : std_logic_array(0 to 3);',
            'end record;',
            'constant TNS_G_TEST_O_RESET : tns_g_test_o_type := (',
            '  f_foo_ready => \'0\',',
            '  f_bar_data => (others => (others => \'0\')),',
            '  f_bar_valid => (others => \'0\')',
            ');',
            'type tns_g_test_g_type is record',
            '  f_foo_enable : boolean;',
            '  f_bar_enable : boolean_array(0 to 3);',
            'end record;',
            'constant TNS_G_TEST_G_RESET : tns_g_test_g_type := (',
            '  f_foo_enable => false,',
            '  f_bar_enable => (others => false)',
            ');',
        ]))
        self.assertEqual(str(foo_d['a']['b']), 'g_test_i.f_foo_data(b)')
        self.assertEqual(str(foo_v['a']['b']), 'g_test_i.f_foo_valid')
        self.assertEqual(str(foo_r['a']['b']), 'g_test_o.f_foo_ready')
        self.assertEqual(str(foo_e['a']['b']), 'G_TEST_G.f_foo_enable')
        self.assertEqual(str(bar_d['a']['b']), 'g_test_o.f_bar_data(a)(b)')
        self.assertEqual(str(bar_v['a']['b']), 'g_test_o.f_bar_valid(a)')
        self.assertEqual(str(bar_r['a']['b']), 'g_test_i.f_bar_ready(a)')
        self.assertEqual(str(bar_e['a']['b']), 'G_TEST_G.f_bar_enable(a)')

    def test_ungrouped_flattened(self):
        """test ungrouped, array-flattened interface generation"""
        result = self.gen_basic_interface(False, True)
        iface, foo_d, foo_v, foo_r, foo_e, bar_d, bar_v, bar_r, bar_e = result
        self.assertEqual('\n\n'.join(iface.generate('port')), '\n'.join([
            '@ Interface for field foo: a scalar field.',
            'f_foo_data : in std_logic_vector(7 downto 0)@:= (others => \'0\');',
            'f_foo_valid : in std_logic@:= \'0\';',
            'f_foo_ready : out std_logic@:= \'0\';',
            '',
            '@ Interface for field bar: a vector field.',
            'f_bar_data : out std_logic_vector(31 downto 0)@:= (others => \'0\');',
            'f_bar_valid : out std_logic_vector(3 downto 0)@:= (others => \'0\');',
            'f_bar_ready : in std_logic_vector(3 downto 0)@:= (others => \'0\');',
        ]))
        result = iface.generate('generic', end_with_semicolon=False)
        self.assertEqual('\n\n'.join(result), '\n'.join([
            '@ Interface for field foo: a scalar field.',
            'F_FOO_ENABLE : boolean@:= false;',
            '',
            '@ Interface for field bar: a vector field.',
            'F_BAR_ENABLE : boolean_array(0 to 3)@:= (others => false)',
        ]))
        self.assertEqual('\n'.join(types.gather_defs(*iface.gather_types())), '\n'.join([
        ]))
        self.assertEqual(str(foo_d['a']['b']), 'f_foo_data(b)')
        self.assertEqual(str(foo_v['a']['b']), 'f_foo_valid')
        self.assertEqual(str(foo_r['a']['b']), 'f_foo_ready')
        self.assertEqual(str(foo_e['a']['b']), 'F_FOO_ENABLE')
        self.assertEqual(str(bar_d['a']['b']), 'f_bar_data(8*a + b)')
        self.assertEqual(str(bar_v['a']['b']), 'f_bar_valid(a)')
        self.assertEqual(str(bar_r['a']['b']), 'f_bar_ready(a)')
        self.assertEqual(str(bar_e['a']['b']), 'F_BAR_ENABLE(a)')

    def test_grouped_flattened(self):
        """test grouped, array-flattened interface generation"""
        result = self.gen_basic_interface('test', True)
        iface, foo_d, foo_v, foo_r, foo_e, bar_d, bar_v, bar_r, bar_e = result
        self.assertEqual('\n\n'.join(iface.generate('port')), '\n'.join([
            '@ Interface group for:',
            '@  - field bar: a vector field.',
            '@  - field foo: a scalar field.',
            'g_test_i : in tns_g_test_i_type@:= TNS_G_TEST_I_RESET;',
            'g_test_o : out tns_g_test_o_type@:= TNS_G_TEST_O_RESET;',
        ]))
        result = iface.generate('generic', end_with_semicolon=False)
        self.assertEqual('\n\n'.join(result), '\n'.join([
            '@ Interface group for:',
            '@  - field bar: a vector field.',
            '@  - field foo: a scalar field.',
            'G_TEST_G : tns_g_test_g_type@:= TNS_G_TEST_G_RESET',
        ]))
        self.assertEqual('\n'.join(types.gather_defs(*iface.gather_types())), '\n'.join([
            'type tns_g_test_i_type is record',
            '  f_foo_data : std_logic_vector(7 downto 0);',
            '  f_foo_valid : std_logic;',
            '  f_bar_ready : std_logic_vector(3 downto 0);',
            'end record;',
            'constant TNS_G_TEST_I_RESET : tns_g_test_i_type := (',
            '  f_foo_data => (others => \'0\'),',
            '  f_foo_valid => \'0\',',
            '  f_bar_ready => (others => \'0\')',
            ');',
            'type tns_g_test_o_type is record',
            '  f_foo_ready : std_logic;',
            '  f_bar_data : std_logic_vector(31 downto 0);',
            '  f_bar_valid : std_logic_vector(3 downto 0);',
            'end record;',
            'constant TNS_G_TEST_O_RESET : tns_g_test_o_type := (',
            '  f_foo_ready => \'0\',',
            '  f_bar_data => (others => \'0\'),',
            '  f_bar_valid => (others => \'0\')',
            ');',
            'type tns_g_test_g_type is record',
            '  f_foo_enable : boolean;',
            '  f_bar_enable : boolean_array(0 to 3);',
            'end record;',
            'constant TNS_G_TEST_G_RESET : tns_g_test_g_type := (',
            '  f_foo_enable => false,',
            '  f_bar_enable => (others => false)',
            ');',
        ]))
        self.assertEqual(str(foo_d['a']['b']), 'g_test_i.f_foo_data(b)')
        self.assertEqual(str(foo_v['a']['b']), 'g_test_i.f_foo_valid')
        self.assertEqual(str(foo_r['a']['b']), 'g_test_o.f_foo_ready')
        self.assertEqual(str(foo_e['a']['b']), 'G_TEST_G.f_foo_enable')
        self.assertEqual(str(bar_d['a']['b']), 'g_test_o.f_bar_data(8*a + b)')
        self.assertEqual(str(bar_v['a']['b']), 'g_test_o.f_bar_valid(a)')
        self.assertEqual(str(bar_r['a']['b']), 'g_test_i.f_bar_ready(a)')
        self.assertEqual(str(bar_e['a']['b']), 'G_TEST_G.f_bar_enable(a)')

    def test_mixed(self):
        """test generation of mixed-mode interface"""

        iface = Interface('tns')

        options = InterfaceOptions(InterfaceConfig(
            group=False, flatten=False,
            generic_group='foo', generic_flatten=True))

        iface.add(
            'foo', 'field foo: a scalar field.', 'f', None,
            'data', 'i', types.std_logic_vector, 8, options)
        iface.add(
            'foo', 'field foo: a scalar field.', 'f', None,
            'valid', 'i', types.std_logic, None, options)
        iface.add(
            'foo', 'field foo: a scalar field.', 'f', None,
            'ready', 'o', types.std_logic, None, options)
        iface.add(
            'foo', 'field foo: a scalar field.', 'f', None,
            'enable', 'g', types.boolean, None, options)

        options = InterfaceOptions(InterfaceConfig(
            group='bar', flatten=True,
            generic_group=False, generic_flatten=False))

        iface.add(
            'bar', 'field bar: a vector field.', 'f', 4,
            'data', 'o', types.std_logic_vector, 8, options)
        iface.add(
            'bar', 'field bar: a vector field.', 'f', 4,
            'valid', 'o', types.std_logic, None, options)
        iface.add(
            'bar', 'field bar: a vector field.', 'f', 4,
            'ready', 'i', types.std_logic, None, options)
        iface.add(
            'bar', 'field bar: a vector field.', 'f', 4,
            'enable', 'g', types.boolean, None, options)

        self.assertEqual('\n\n'.join(iface.generate('port')), '\n'.join([
            '@ Interface for field foo: a scalar field.',
            'f_foo_i : in tns_f_foo_i_type@:= TNS_F_FOO_I_RESET;',
            'f_foo_o : out tns_f_foo_o_type@:= TNS_F_FOO_O_RESET;',
            '',
            '@ Interface group for:',
            '@  - field bar: a vector field.',
            'g_bar_o : out tns_g_bar_o_type@:= TNS_G_BAR_O_RESET;',
            'g_bar_i : in tns_g_bar_i_type@:= TNS_G_BAR_I_RESET;',
        ]))
        result = iface.generate('generic', end_with_semicolon=False)
        self.assertEqual('\n\n'.join(result), '\n'.join([
            '@ Interface group for:',
            '@  - field foo: a scalar field.',
            'G_FOO_G : tns_g_foo_g_type@:= TNS_G_FOO_G_RESET;',
            '',
            '@ Interface for field bar: a vector field.',
            'F_BAR_G : tns_f_bar_g_array(0 to 3)@:= (others => TNS_F_BAR_G_RESET)',
        ]))
        self.assertEqual('\n'.join(types.gather_defs(*iface.gather_types())), '\n'.join([
            'type tns_f_foo_i_type is record',
            '  data : std_logic_vector(7 downto 0);',
            '  valid : std_logic;',
            'end record;',
            'constant TNS_F_FOO_I_RESET : tns_f_foo_i_type := (',
            '  data => (others => \'0\'),',
            '  valid => \'0\'',
            ');',
            'type tns_f_foo_o_type is record',
            '  ready : std_logic;',
            'end record;',
            'constant TNS_F_FOO_O_RESET : tns_f_foo_o_type := (',
            '  ready => \'0\'',
            ');',
            'type tns_g_foo_g_type is record',
            '  f_foo_enable : boolean;',
            'end record;',
            'constant TNS_G_FOO_G_RESET : tns_g_foo_g_type := (',
            '  f_foo_enable => false',
            ');',
            'type tns_g_bar_o_type is record',
            '  f_bar_data : std_logic_vector(31 downto 0);',
            '  f_bar_valid : std_logic_vector(3 downto 0);',
            'end record;',
            'constant TNS_G_BAR_O_RESET : tns_g_bar_o_type := (',
            '  f_bar_data => (others => \'0\'),',
            '  f_bar_valid => (others => \'0\')',
            ');',
            'type tns_g_bar_i_type is record',
            '  f_bar_ready : std_logic_vector(3 downto 0);',
            'end record;',
            'constant TNS_G_BAR_I_RESET : tns_g_bar_i_type := (',
            '  f_bar_ready => (others => \'0\')',
            ');',
            'type tns_f_bar_g_type is record',
            '  enable : boolean;',
            'end record;',
            'constant TNS_F_BAR_G_RESET : tns_f_bar_g_type := (',
            '  enable => false',
            ');',
            'type tns_f_bar_g_array is array (natural range <>) of tns_f_bar_g_type;',
        ]))

    def test_type_inference(self):
        """test interface generator VHDL type inference"""

        options = InterfaceOptions(InterfaceConfig(
            group=False, flatten=True,
            generic_group=False, generic_flatten=True))

        for count, abs_type, vhd_type in [
                (8, types.StdLogicVector, 'std_logic_vector(7 downto 0)@:= (others => \'0\')'),
                (1, types.StdLogicVector, 'std_logic_vector(0 downto 0)@:= (others => \'0\')'),
                (None, types.StdLogic, 'std_logic@:= \'0\'')]:

            iface = Interface('tns')
            obj = iface.add(
                'foo', 'field foo: a scalar field.', 'f', None,
                'data', 'i', None, count, options)
            self.assertTrue(isinstance(obj.typ, abs_type))
            self.assertEqual('\n\n'.join(iface.generate('port')), '\n'.join([
                '@ Interface for field foo: a scalar field.',
                'f_foo_data : in %s;' % vhd_type,
            ]))

    def test_type_errors(self):
        """test interface generator VHDL type errors"""

        iface = Interface('tns')

        with self.assertRaisesRegex(
                ValueError,
                'signal count is not None, but signal type is not an incomplete array'):
            iface.add(
                'foo', 'field foo: a scalar field.', 'f', None,
                'data', 'i', types.std_logic, 8,
                InterfaceOptions(InterfaceConfig()))

        with self.assertRaisesRegex(
                ValueError,
                'signal type is an incomplete array, but signal count is None'):
            iface.add(
                'foo', 'field foo: a scalar field.', 'f', None,
                'data', 'i', types.std_logic_vector, None,
                InterfaceOptions(InterfaceConfig()))
