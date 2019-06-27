from unittest import TestCase
import os
import tempfile
from collections import OrderedDict

import vhdmmio.vhdl.types as types

class TestVhdlTypes(TestCase):

    def test_std_logic(self):
        self.assertEqual(types.std_logic.name, 'std_logic')
        self.assertEqual(str(types.std_logic), 'std_logic')
        self.assertEqual(len(types.std_logic), 1)
        self.assertEqual(types.std_logic.get_defs(), [])
        self.assertEqual(list(types.std_logic.gather_types()), [])
        self.assertEqual(types.std_logic.default, "'0'")

    def test_boolean(self):
        self.assertEqual(types.boolean.name, 'boolean')
        self.assertEqual(str(types.boolean), 'boolean')
        with self.assertRaises(ValueError):
            len(types.boolean)
        self.assertEqual(types.boolean.get_defs(), [])
        self.assertEqual(list(types.boolean.gather_types()), [])
        self.assertEqual(types.boolean.default, 'false')
        self.assertEqual(types.Boolean(True).default, 'true')

    def test_natural(self):
        self.assertEqual(types.natural.name, 'natural')
        self.assertEqual(str(types.natural), 'natural')
        with self.assertRaises(ValueError):
            len(types.natural)
        self.assertEqual(types.natural.get_defs(), [])
        self.assertEqual(list(types.natural.gather_types()), [])
        self.assertEqual(types.natural.default, '0')

    def test_std_logic_vector(self):
        self.assertEqual(types.std_logic_vector.name, 'std_logic_vector')
        self.assertEqual(str(types.std_logic_vector), 'std_logic_vector')
        with self.assertRaises(ValueError):
            len(types.std_logic_vector)
        self.assertEqual(types.std_logic_vector.get_defs(), [])
        self.assertEqual(list(types.std_logic_vector.gather_types()), [])
        self.assertEqual(types.std_logic_vector.default, "(others => '0')")
        self.assertEqual(types.std_logic_vector.get_range(8), '7 downto 0')

        self.assertEqual(
            types.std_logic_vector.make_signal('test', '"0101"')[0],
            'signal test : std_logic_vector(3 downto 0)@:= "0101"')

        typ = types.SizedArray('test', types.std_logic_vector, '"1111000011001010"')
        self.assertEqual(typ.name, 'test')
        self.assertEqual(str(typ), 'test_type')
        self.assertEqual(len(typ), 16)
        self.assertEqual(typ.get_defs(), [
            'subtype test_type is std_logic_vector(15 downto 0);'
        ])
        self.assertEqual(list(typ.gather_types()), ['test_type'])
        self.assertEqual(typ.default, '"1111000011001010"')

    def test_std_logic_array(self):
        array = types.Array('test', types.std_logic)
        self.assertEqual(array.name, 'test')
        self.assertEqual(str(array), 'test_array')
        with self.assertRaises(ValueError):
            len(array)
        self.assertEqual(array.get_defs(), [
            'type test_array is array (natural range <>) of std_logic;'
        ])
        self.assertEqual(list(array.gather_types()), ['test_array'])
        self.assertEqual(array.default, "(others => '0')")
        self.assertEqual(array.get_range(8), '0 to 7')

    def test_sized_std_logic_array(self):
        array = types.SizedArray('test', types.std_logic, 8)
        self.assertEqual(array.name, 'test')
        self.assertEqual(str(array), 'test_type')
        self.assertEqual(len(array), 8)
        self.assertEqual(types.gather_defs(array), [
            'type std_logic_array is array (natural range <>) of std_logic;',
            'subtype test_type is std_logic_array(0 to 7);',
        ])
        self.assertEqual(list(array.gather_types()), ['std_logic_array', 'test_type'])
        self.assertEqual(array.default, "(others => '0')")

    def test_memory(self):
        typ = types.SizedArray('mem_ent', types.StdLogicVector('U'), 8)
        self.assertEqual(typ.name, 'mem_ent')
        self.assertEqual(str(typ), 'mem_ent_type')
        self.assertEqual(len(typ), 8)
        self.assertEqual(typ.get_defs(), [
            'subtype mem_ent_type is std_logic_vector(7 downto 0);'
        ])
        self.assertEqual(list(typ.gather_types()), ['mem_ent_type'])
        self.assertEqual(typ.default, "(others => 'U')")

        typ = types.Array('mem', typ)
        self.assertEqual(typ.name, 'mem')
        self.assertEqual(str(typ), 'mem_array')
        with self.assertRaises(ValueError):
            len(typ)
        self.assertEqual(typ.get_defs(), [
            'type mem_array is array (natural range <>) of mem_ent_type;'
        ])
        self.assertEqual(list(typ.gather_types()), ['mem_ent_type', 'mem_array'])
        self.assertEqual(typ.default, "(others => (others => 'U'))")
        self.assertEqual(typ.get_range(8), '0 to 7')

        self.assertEqual(
            typ.make_signal('test', ['X"%02X"' % idx for idx in range(4)])[0],
            'signal test : mem_array(0 to 3)@:= (0 => X"00",@1 => X"01",@2 => X"02",@3 => X"03")')

        typ = types.SizedArray('mem', typ, ['X"%02X"' % idx for idx in range(4)])
        self.assertEqual(typ.name, 'mem')
        self.assertEqual(str(typ), 'mem_type')
        self.assertEqual(len(typ), 32)
        self.assertEqual(typ.get_defs(), [
            'subtype mem_type is mem_array(0 to 3);',
            'constant MEM_RESET : mem_type@:= (0 => X"00",@1 => X"01",@2 => X"02",@3 => X"03");',
        ])
        self.assertEqual(list(typ.gather_types()), ['mem_ent_type', 'mem_array', 'mem_type'])
        self.assertEqual(typ.default, 'MEM_RESET')

    def test_record(self):
        self.maxDiff = None
        byte_type = types.SizedArray('byte', types.std_logic_vector, 8)
        byte_array = types.Array('byte', byte_type)
        record = types.Record('test', ('a', byte_type))
        with self.assertRaisesRegex(ValueError, 'name conflict'):
            record.append('a', types.std_logic)
        record.append('b', types.std_logic)
        record.append('c', types.std_logic_vector, '"0011"')
        record.append('d', types.std_logic, '1')
        record.append('e', byte_array, ['X"01"', 'X"02"', 'X"03"', 'X"04"'])
        self.assertEqual(record.name, 'test')
        self.assertEqual(str(record), 'test_type')
        self.assertEqual(len(record), 46)
        self.assertEqual(types.gather_defs(record, byte_type, byte_type), [
            'subtype byte_type is std_logic_vector(7 downto 0);',
            'type byte_array is array (natural range <>) of byte_type;',
            'subtype test_e_type is byte_array(0 to 3);',
            'constant TEST_E_RESET : test_e_type@:= (0 => X"01",@1 => X"02",@2 => X"03",@3 => X"04");',
            'type test_type is record',
            '  a : byte_type;',
            '  b : std_logic;',
            '  c : std_logic_vector(3 downto 0);',
            '  d : std_logic;',
            '  e : test_e_type;',
            'end record;',
            'constant TEST_RESET : test_type := (',
            "  a => (others => '0'),",
            "  b => '0',",
            '  c => "0011",',
            '  d => 1,',
            '  e => TEST_E_RESET',
            ');',
        ])
        byte_type = types.SizedArray('byte', types.std_logic_vector, 7)
        with self.assertRaisesRegex(ValueError, 'name conflict'):
            types.gather_defs(record, byte_type)
        byte_type = types.SizedArray('byte', types.std_logic_vector, 8)
        types.gather_defs(record, byte_type)
        self.assertEqual(record.default, 'TEST_RESET')

        self.assertEqual(record.make_input('test')[0], 'test : in test_type@:= TEST_RESET')
        self.assertEqual(record.make_output('test')[0], 'test : out test_type@:= TEST_RESET')
        self.assertEqual(record.make_signal('test')[0], 'signal test : test_type@:= TEST_RESET')
        self.assertEqual(record.make_variable('test')[0], 'variable test : test_type@:= TEST_RESET')
        self.assertEqual(record.make_constant('test')[0], 'constant TEST : test_type@:= TEST_RESET')
        self.assertEqual(record.make_generic('test')[0], 'TEST : test_type@:= TEST_RESET')
        self.assertEqual(record.make_generic('test', 'foo')[0], 'TEST : test_type@:= foo')

        _, test = record.make_input('test')
        self.assertEqual(str(test), 'test')
        self.assertEqual(str(test.typ), 'test_type')
        self.assertEqual(str(test.a), 'test.a')
        self.assertEqual(str(test.a.typ), 'byte_type')
        self.assertEqual(str(test.a[0]), 'test.a(0)')
        self.assertEqual(str(test.a[0].typ), 'std_logic')
        self.assertEqual(str(test.a[2, 3]), 'test.a(4 downto 2)')
        self.assertEqual(str(test.a[2, 3].typ), '<slice of std_logic>')
        self.assertEqual(str(test.a[2, 3].typ.count), '3')
        self.assertEqual(str(test.a[2, 'test']), 'test.a(test + 1 downto 2)')
        self.assertEqual(str(test.a[2, 'test'].typ.count), 'test')
        self.assertEqual(str(test.a[1, 'test']), 'test.a(test downto 1)')
        self.assertEqual(str(test.a[0, 'test']), 'test.a(test - 1 downto 0)')
        self.assertEqual(str(test.a[0, 'foo + bar']), 'test.a((foo + bar) - 1 downto 0)')
        self.assertEqual(str(test.a['test', 3]), 'test.a(test + 2 downto test)')
        self.assertEqual(str(test.a['foo + bar', 5]), 'test.a((foo + bar) + 4 downto (foo + bar))')
        self.assertEqual(str(test.a['foo', 'bar']), 'test.a(foo + bar - 1 downto foo)')
        self.assertEqual(str(test.b['foo', 'bar']), '(bar - 1 downto 0 => test.b)')
        self.assertEqual(str(test.b[0]), str(test.b))

        with self.assertRaises(AttributeError):
            test.a.a
        with self.assertRaises(AttributeError):
            test.f
        record.append('f', types.std_logic)
        self.assertEqual(str(test.f), 'test.f')

    def test_abstracted_object(self):
        data_typ = types.std_logic_vector
        foo_typ = types.Record('foo', ('data', data_typ, 8))
        foo_arr = types.Array('foo', foo_typ)
        bar_typ = types.Record('bar', ('foo', foo_arr, 4))
        obj = types.Object('bar', data_typ, ['foo', (foo_arr, [4]), 'data'])

        self.assertEqual(str(obj), str('bar.foo'))
        self.assertEqual(obj.typ, foo_arr)
        self.assertTrue(obj.abstracted)
        self.assertEqual(str(obj[0, 2]), str('bar.foo(0 to 1)'))
        self.assertEqual(str(obj['a', 'b']), str('bar.foo(a to a + b - 1)'))
        self.assertEqual(str(obj[1]), str('bar.foo(1).data'))
        self.assertEqual(str(obj['a']), str('bar.foo(a).data'))
        self.assertEqual(obj[1].typ, data_typ)
        self.assertFalse(obj[1].abstracted)
        self.assertEqual(str(obj[1][0, 4]), str('bar.foo(1).data(3 downto 0)'))
        self.assertEqual(str(obj['a']['b', 'c']), str('bar.foo(a).data(b + c - 1 downto b)'))
        self.assertEqual(str(obj[1][5]), str('bar.foo(1).data(5)'))
        self.assertEqual(str(obj['a']['b']), str('bar.foo(a).data(b)'))
        self.assertEqual(obj[1][5].typ.name, types.std_logic.name)
        self.assertFalse(obj[1][5].abstracted)

        data_typ = types.std_logic_vector
        bar_typ = types.Record('bar', ('foo_data', data_typ, 32))
        obj = types.Object('bar', types.std_logic, ['foo_data', (data_typ, [4, 8])])

        self.assertEqual(str(obj), str('bar.foo_data'))
        self.assertEqual(obj.typ, data_typ)
        self.assertTrue(obj.abstracted)
        self.assertEqual(str(obj[0, 2]), str('bar.foo_data(15 downto 0)'))
        self.assertEqual(str(obj['a', 'b']), str('bar.foo_data(8*a + 8*b - 1 downto 8*a)'))
        self.assertEqual(str(obj[1]), str('bar.foo_data(15 downto 8)'))
        self.assertEqual(str(obj['a']), str('bar.foo_data(8*a + 7 downto 8*a)'))
        self.assertEqual(obj[1].typ, data_typ)
        self.assertTrue(obj[1].abstracted)
        self.assertEqual(str(obj[1][0, 4]), str('bar.foo_data(11 downto 8)'))
        self.assertEqual(str(obj['a']['b', 'c']), str('bar.foo_data(8*a + b + c - 1 downto 8*a + b)'))
        self.assertEqual(str(obj[1][5]), str('bar.foo_data(13)'))
        self.assertEqual(str(obj['a']['b']), str('bar.foo_data(8*a + b)'))
        self.assertEqual(obj[1][5].typ.name, types.std_logic.name)
        self.assertFalse(obj[1][5].abstracted)

        data_typ = types.std_logic_vector
        bar_typ = types.Record('bar', ('foo_data', data_typ, 8))
        obj = types.Object(None, types.std_logic, ['bar', 'foo_data', (bar_typ, None), (data_typ, [8])])

        self.assertEqual(str(obj), str('bar.foo_data'))
        self.assertEqual(obj.typ, bar_typ)
        self.assertTrue(obj.abstracted)
        self.assertEqual(str(obj[0, 2]), str('(0 to 1 => bar.foo_data)'))
        self.assertEqual(str(obj['a', 'b']), str('(0 to b - 1 => bar.foo_data)'))
        self.assertEqual(str(obj[1]), str('bar.foo_data'))
        self.assertEqual(str(obj['a']), str('bar.foo_data'))
        self.assertEqual(obj[1].typ, data_typ)
        self.assertTrue(obj[1].abstracted)
        self.assertEqual(str(obj[1][0, 4]), str('bar.foo_data(3 downto 0)'))
        self.assertEqual(str(obj['a']['b', 'c']), str('bar.foo_data(b + c - 1 downto b)'))
        self.assertEqual(str(obj[1][5]), str('bar.foo_data(5)'))
        self.assertEqual(str(obj['a']['b']), str('bar.foo_data(b)'))
        self.assertEqual(obj[1][5].typ.name, types.std_logic.name)
        self.assertFalse(obj[1][5].abstracted)
