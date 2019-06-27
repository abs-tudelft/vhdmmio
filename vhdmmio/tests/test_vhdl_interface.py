from unittest import TestCase
import os
import tempfile
from collections import OrderedDict

import vhdmmio.vhdl.types as types
from vhdmmio.vhdl.interface import Interface

class TestVhdlInterface(TestCase):

    maxDiff = None

    @staticmethod
    def gen_basic_interface(group, flatten):
        iface = Interface('tns', group, flatten)

        objs = [iface]

        objs.append(iface.add(
            'foo', 'field foo: a scalar field.', 'f', None,
            'data', 'i', types.std_logic_vector, 8))
        objs.append(iface.add(
            'foo', 'field foo: a scalar field.', 'f', None,
            'valid', 'i', types.std_logic, None))
        objs.append(iface.add(
            'foo', 'field foo: a scalar field.', 'f', None,
            'ready', 'o', types.std_logic, None))
        objs.append(iface.add(
            'foo', 'field foo: a scalar field.', 'f', None,
            'enable', 'g', types.boolean, None))

        objs.append(iface.add(
            'bar', 'field bar: a vector field.', 'f', 4,
            'data', 'o', types.std_logic_vector, 8))
        objs.append(iface.add(
            'bar', 'field bar: a vector field.', 'f', 4,
            'valid', 'o', types.std_logic, None))
        objs.append(iface.add(
            'bar', 'field bar: a vector field.', 'f', 4,
            'ready', 'i', types.std_logic, None))
        objs.append(iface.add(
            'bar', 'field bar: a vector field.', 'f', 4,
            'enable', 'g', types.boolean, None))

        return tuple(objs)

    def test_ungrouped_unflattened(self):
        iface, fd, fv, fr, fe, bd, bv, br, be = self.gen_basic_interface(False, 'never')
        self.assertEqual('\n\n'.join(iface.generate('port')), '\n'.join([
            '@ Interface for field foo: a scalar field.',
            'f_foo_i : in tns_f_foo_i_type@:= TNS_F_FOO_I_RESET;',
            'f_foo_o : out tns_f_foo_o_type@:= TNS_F_FOO_O_RESET;',
            '',
            '@ Interface for field bar: a vector field.',
            'f_bar_o : out tns_f_bar_o_array(0 to 3)@:= (others => TNS_F_BAR_O_RESET);',
            'f_bar_i : in tns_f_bar_i_array(0 to 3)@:= (others => TNS_F_BAR_I_RESET);',
        ]))
        self.assertEqual('\n\n'.join(iface.generate('generic', end_with_semicolon=False)), '\n'.join([
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
        self.assertEqual(str(fd['a']['b']), 'f_foo_i.data(b)')
        self.assertEqual(str(fv['a']['b']), 'f_foo_i.valid')
        self.assertEqual(str(fr['a']['b']), 'f_foo_o.ready')
        self.assertEqual(str(bd['a']['b']), 'f_bar_o(a).data(b)')
        self.assertEqual(str(bv['a']['b']), 'f_bar_o(a).valid')
        self.assertEqual(str(br['a']['b']), 'f_bar_i(a).ready')

    def test_grouped_unflattened(self):
        iface, fd, fv, fr, fe, bd, bv, br, be = self.gen_basic_interface('test', 'never')
        self.assertEqual('\n\n'.join(iface.generate('port')), '\n'.join([
            '@ Interface group for:',
            '@  - field bar: a vector field.',
            '@  - field foo: a scalar field.',
            'g_test_i : in tns_g_test_i_type@:= TNS_G_TEST_I_RESET;',
            'g_test_o : out tns_g_test_o_type@:= TNS_G_TEST_O_RESET;',
        ]))
        self.assertEqual('\n\n'.join(iface.generate('generic', end_with_semicolon=False)), '\n'.join([
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
        self.assertEqual(str(fd['a']['b']), 'g_test_i.f_foo.data(b)')
        self.assertEqual(str(fv['a']['b']), 'g_test_i.f_foo.valid')
        self.assertEqual(str(fr['a']['b']), 'g_test_o.f_foo.ready')
        self.assertEqual(str(bd['a']['b']), 'g_test_o.f_bar(a).data(b)')
        self.assertEqual(str(bv['a']['b']), 'g_test_o.f_bar(a).valid')
        self.assertEqual(str(br['a']['b']), 'g_test_i.f_bar(a).ready')

    def test_ungrouped_flattened_records(self):
        iface, fd, fv, fr, fe, bd, bv, br, be = self.gen_basic_interface(False, 'record')
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
        self.assertEqual('\n\n'.join(iface.generate('generic', end_with_semicolon=False)), '\n'.join([
            '@ Interface for field foo: a scalar field.',
            'F_FOO_ENABLE : boolean@:= false;',
            '',
            '@ Interface for field bar: a vector field.',
            'F_BAR_ENABLE : boolean_array(0 to 3)@:= (others => false)',
        ]))
        self.assertEqual('\n'.join(types.gather_defs(*iface.gather_types())), '\n'.join([
            'subtype tns_f_bar_data_type is std_logic_vector(7 downto 0);',
            'type tns_f_bar_data_array is array (natural range <>) of tns_f_bar_data_type;',
            'type std_logic_array is array (natural range <>) of std_logic;',
            'type boolean_array is array (natural range <>) of boolean;',
        ]))
        self.assertEqual(str(fd['a']['b']), 'f_foo_data(b)')
        self.assertEqual(str(fv['a']['b']), 'f_foo_valid')
        self.assertEqual(str(fr['a']['b']), 'f_foo_ready')
        self.assertEqual(str(bd['a']['b']), 'f_bar_data(a)(b)')
        self.assertEqual(str(bv['a']['b']), 'f_bar_valid(a)')
        self.assertEqual(str(br['a']['b']), 'f_bar_ready(a)')

    def test_grouped_flattened_records(self):
        iface, fd, fv, fr, fe, bd, bv, br, be = self.gen_basic_interface('test', 'record')
        self.assertEqual('\n\n'.join(iface.generate('port')), '\n'.join([
            '@ Interface group for:',
            '@  - field bar: a vector field.',
            '@  - field foo: a scalar field.',
            'g_test_i : in tns_g_test_i_type@:= TNS_G_TEST_I_RESET;',
            'g_test_o : out tns_g_test_o_type@:= TNS_G_TEST_O_RESET;',
        ]))
        self.assertEqual('\n\n'.join(iface.generate('generic', end_with_semicolon=False)), '\n'.join([
            '@ Interface group for:',
            '@  - field bar: a vector field.',
            '@  - field foo: a scalar field.',
            'G_TEST_G : tns_g_test_g_type@:= TNS_G_TEST_G_RESET',
        ]))
        self.assertEqual('\n'.join(types.gather_defs(*iface.gather_types())), '\n'.join([
            'type std_logic_array is array (natural range <>) of std_logic;',
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
            'type boolean_array is array (natural range <>) of boolean;',
            'type tns_g_test_g_type is record',
            '  f_foo_enable : boolean;',
            '  f_bar_enable : boolean_array(0 to 3);',
            'end record;',
            'constant TNS_G_TEST_G_RESET : tns_g_test_g_type := (',
            '  f_foo_enable => false,',
            '  f_bar_enable => (others => false)',
            ');',
        ]))
        self.assertEqual(str(fd['a']['b']), 'g_test_i.f_foo_data(b)')
        self.assertEqual(str(fv['a']['b']), 'g_test_i.f_foo_valid')
        self.assertEqual(str(fr['a']['b']), 'g_test_o.f_foo_ready')
        self.assertEqual(str(bd['a']['b']), 'g_test_o.f_bar_data(a)(b)')
        self.assertEqual(str(bv['a']['b']), 'g_test_o.f_bar_valid(a)')
        self.assertEqual(str(br['a']['b']), 'g_test_i.f_bar_ready(a)')

    def test_ungrouped_flattened(self):
        iface, fd, fv, fr, fe, bd, bv, br, be = self.gen_basic_interface(False, 'all')
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
        self.assertEqual('\n\n'.join(iface.generate('generic', end_with_semicolon=False)), '\n'.join([
            '@ Interface for field foo: a scalar field.',
            'F_FOO_ENABLE : boolean@:= false;',
            '',
            '@ Interface for field bar: a vector field.',
            'F_BAR_ENABLE : boolean_array(0 to 3)@:= (others => false)',
        ]))
        self.assertEqual('\n'.join(types.gather_defs(*iface.gather_types())), '\n'.join([
            'type boolean_array is array (natural range <>) of boolean;',
        ]))
        self.assertEqual(str(fd['a']['b']), 'f_foo_data(b)')
        self.assertEqual(str(fv['a']['b']), 'f_foo_valid')
        self.assertEqual(str(fr['a']['b']), 'f_foo_ready')
        self.assertEqual(str(bd['a']['b']), 'f_bar_data(8*a + b)')
        self.assertEqual(str(bv['a']['b']), 'f_bar_valid(a)')
        self.assertEqual(str(br['a']['b']), 'f_bar_ready(a)')

    def test_grouped_flattened(self):
        iface, fd, fv, fr, fe, bd, bv, br, be = self.gen_basic_interface('test', 'all')
        self.assertEqual('\n\n'.join(iface.generate('port')), '\n'.join([
            '@ Interface group for:',
            '@  - field bar: a vector field.',
            '@  - field foo: a scalar field.',
            'g_test_i : in tns_g_test_i_type@:= TNS_G_TEST_I_RESET;',
            'g_test_o : out tns_g_test_o_type@:= TNS_G_TEST_O_RESET;',
        ]))
        self.assertEqual('\n\n'.join(iface.generate('generic', end_with_semicolon=False)), '\n'.join([
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
            'type boolean_array is array (natural range <>) of boolean;',
            'type tns_g_test_g_type is record',
            '  f_foo_enable : boolean;',
            '  f_bar_enable : boolean_array(0 to 3);',
            'end record;',
            'constant TNS_G_TEST_G_RESET : tns_g_test_g_type := (',
            '  f_foo_enable => false,',
            '  f_bar_enable => (others => false)',
            ');',
        ]))
        self.assertEqual(str(fd['a']['b']), 'g_test_i.f_foo_data(b)')
        self.assertEqual(str(fv['a']['b']), 'g_test_i.f_foo_valid')
        self.assertEqual(str(fr['a']['b']), 'g_test_o.f_foo_ready')
        self.assertEqual(str(bd['a']['b']), 'g_test_o.f_bar_data(8*a + b)')
        self.assertEqual(str(bv['a']['b']), 'g_test_o.f_bar_valid(a)')
        self.assertEqual(str(br['a']['b']), 'g_test_i.f_bar_ready(a)')
