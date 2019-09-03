"""Custom field tests."""

from unittest import TestCase
from ..testbench import RegisterFileTestbench

class TestCustomFields(TestCase):
    """Custom field tests"""

    def test_basic(self):
        """test basic custom fields"""
        rft = RegisterFileTestbench({
            'metadata': {'name': 'test'},
            'fields': [
                {
                    'address': 0,
                    'name': 'a',
                    'behavior': 'custom',
                    'read': (
                        '$ack$ := true;\n'
                        '$data$ := X"11223344";\n'
                    )
                },
                {
                    'address': 4,
                    'name': 'b',
                    'behavior': 'custom',
                    'write': (
                        'if $data$(0) = \'0\' then\n'
                        '  $ack$ := true;\n'
                        'else\n'
                        '  $nack$ := true;\n'
                        'end if;\n'
                    )
                },
            ]})
        self.assertEqual(rft.ports, ('bus',))
        with rft as objs:
            self.assertEqual(objs.bus.read(0), 0x11223344)
            with self.assertRaisesRegex(ValueError, 'decode'):
                objs.bus.write(0, 0)

            objs.bus.write(4, 0x11223344)
            with self.assertRaisesRegex(ValueError, 'slave'):
                objs.bus.write(4, 0x44332211)
            with self.assertRaisesRegex(ValueError, 'decode'):
                objs.bus.read(4)

    def test_io(self):
        """test custom field ports and generics"""
        rft = RegisterFileTestbench({
            'metadata': {'name': 'test'},
            'fields': [
                {
                    'address': 0,
                    'repeat': 2,
                    'field-repeat': 1,
                    'name': 'a',
                    'behavior': 'custom',
                    'interfaces': [
                        {'input': 'read_data:32'},
                        {'output': 'write_data:32'},
                        {'output': 'read_toggle'},
                        {'output': 'write_toggle'},
                        {'generic': 'write_reset:32'},
                    ],
                    'read': (
                        '$data$ := $s.read_data$;\n'
                        '$ack$ := true;\n'
                        '$s.read_toggle$ <= not $s.read_toggle$;'
                    ),
                    'write': (
                        '$s.write_data$ <= $data$;\n'
                        '$ack$ := true;\n'
                        '$s.write_toggle$ <= not $s.write_toggle$;'
                    ),
                    'post-access': (
                        'if reset = \'1\' then'
                        '  $s.read_toggle$ <= \'0\';\n'
                        '  $s.write_toggle$ <= \'0\';\n'
                        '  $s.write_data$ <= std_logic_vector(unsigned($s.write_reset$) + $i$);\n'
                        'end if;\n'
                    ),
                },
                {
                    'address': 8,
                    'name': 'b',
                    'behavior': 'custom',
                    'interfaces': [
                        {'input': 'read_data:32'},
                        {'output': 'write_data:32'},
                        {'output': 'read_toggle'},
                        {'output': 'write_toggle'},
                        {'generic': 'write_reset:32'},
                    ],
                    'read': (
                        '$data$ := $s.read_data$;\n'
                        '$ack$ := true;\n'
                        '$s.read_toggle$ <= not $s.read_toggle$;'
                    ),
                    'write': (
                        '$s.write_data$ <= $data$;\n'
                        '$ack$ := true;\n'
                        '$s.write_toggle$ <= not $s.write_toggle$;'
                    ),
                    'post-access': (
                        'if reset = \'1\' then\n'
                        '  $s.read_toggle$ <= \'0\';\n'
                        '  $s.write_toggle$ <= \'0\';\n'
                        '  $s.write_data$ <= std_logic_vector(unsigned($s.write_reset$) + $i$);\n'
                        'end if;\n'
                    ),
                },
            ]}, ('F_A_WRITE_RESET', 'X"4433221111223344"'))
        self.assertEqual(rft.ports, (
            'F_A_WRITE_RESET',
            'F_B_WRITE_RESET',
            'bus',
            'f_a_i.0.read_data',
            'f_a_i.1.read_data',
            'f_a_o.0.read_toggle',
            'f_a_o.0.write_data',
            'f_a_o.0.write_toggle',
            'f_a_o.1.read_toggle',
            'f_a_o.1.write_data',
            'f_a_o.1.write_toggle',
            'f_b_i.read_data',
            'f_b_o.read_toggle',
            'f_b_o.write_data',
            'f_b_o.write_toggle',
        ))
        with rft as objs:
            self.assertEqual(int(objs.f_a_o[0].read_toggle), 0)
            self.assertEqual(int(objs.f_a_o[0].write_toggle), 0)
            self.assertEqual(int(objs.f_a_o[0].write_data), 0x11223344)
            self.assertEqual(int(objs.f_a_o[1].read_toggle), 0)
            self.assertEqual(int(objs.f_a_o[1].write_toggle), 0)
            self.assertEqual(int(objs.f_a_o[1].write_data), 0x44332212)
            self.assertEqual(int(objs.f_b_o.read_toggle), 0)
            self.assertEqual(int(objs.f_b_o.write_toggle), 0)
            self.assertEqual(int(objs.f_b_o.write_data), 0x00000000)

            objs.f_a_i[0].read_data.val = 55
            objs.f_a_i[1].read_data.val = 66
            objs.f_b_i.read_data.val = 77

            self.assertEqual(objs.bus.read(0), 55)
            self.assertEqual(int(objs.f_a_o[0].read_toggle), 1)
            self.assertEqual(int(objs.f_a_o[1].read_toggle), 0)
            self.assertEqual(int(objs.f_b_o.read_toggle), 0)
            self.assertEqual(objs.bus.read(4), 66)
            self.assertEqual(int(objs.f_a_o[0].read_toggle), 1)
            self.assertEqual(int(objs.f_a_o[1].read_toggle), 1)
            self.assertEqual(int(objs.f_b_o.read_toggle), 0)
            self.assertEqual(objs.bus.read(8), 77)
            self.assertEqual(int(objs.f_a_o[0].read_toggle), 1)
            self.assertEqual(int(objs.f_a_o[1].read_toggle), 1)
            self.assertEqual(int(objs.f_b_o.read_toggle), 1)

            objs.bus.write(0, 33)
            self.assertEqual(int(objs.f_a_o[0].write_toggle), 1)
            self.assertEqual(int(objs.f_a_o[1].write_toggle), 0)
            self.assertEqual(int(objs.f_b_o.write_toggle), 0)
            self.assertEqual(int(objs.f_a_o[0].write_data), 33)
            objs.bus.write(4, 42)
            self.assertEqual(int(objs.f_a_o[0].write_toggle), 1)
            self.assertEqual(int(objs.f_a_o[1].write_toggle), 1)
            self.assertEqual(int(objs.f_b_o.write_toggle), 0)
            self.assertEqual(int(objs.f_a_o[1].write_data), 42)
            objs.bus.write(8, 25)
            self.assertEqual(int(objs.f_a_o[0].write_toggle), 1)
            self.assertEqual(int(objs.f_a_o[1].write_toggle), 1)
            self.assertEqual(int(objs.f_b_o.write_toggle), 1)
            self.assertEqual(int(objs.f_b_o.write_data), 25)

    def test_state(self):
        """test custom field state and non-std_logic types"""
        rft = RegisterFileTestbench({
            'metadata': {'name': 'test'},
            'fields': [
                {
                    'address': 0,
                    'repeat': 2,
                    'field-repeat': 1,
                    'name': 'a',
                    'behavior': 'custom',
                    'interfaces': [
                        {'state': 'data:32'},
                        {'state': 'toggle'},
                        {'generic': 'reset', 'type': 'natural'},
                    ],
                    'read': (
                        'if $s.toggle$ = \'0\' then\n'
                        '  $data$ := $s.data$;\n'
                        'else\n'
                        '  $data$ := not $s.data$;\n'
                        'end if;\n'
                        '$s.toggle$ := not $s.toggle$;\n'
                        '$ack$ := true;\n'
                    ),
                    'write': (
                        '$s.data$ := $data$;\n'
                        '$ack$ := true;\n'
                    ),
                    'post-access': (
                        'if reset = \'1\' then'
                        '  $s.toggle$ := \'0\';\n'
                        '  $s.data$ := std_logic_vector(to_unsigned($s.reset$, 32));\n'
                        'end if;\n'
                    ),
                },
            ]}, ('F_A_RESET', '(0 => 33, 1 => 42)'))
        self.assertEqual(rft.ports, (
            'F_A_RESET',
            'bus',
        ))
        with rft as objs:
            self.assertEqual(objs.bus.read(0), 0x00000021)
            self.assertEqual(objs.bus.read(4), 0x0000002A)
            self.assertEqual(objs.bus.read(0), 0xFFFFFFDE)
            self.assertEqual(objs.bus.read(4), 0xFFFFFFD5)
            objs.bus.write(0, 0x33333333)
            objs.bus.write(4, 0x42424242)
            self.assertEqual(objs.bus.read(0), 0x33333333)
            self.assertEqual(objs.bus.read(4), 0x42424242)
            self.assertEqual(objs.bus.read(0), 0xCCCCCCCC)
            self.assertEqual(objs.bus.read(4), 0xBDBDBDBD)

    def test_internals(self):
        """test custom field internal connectivity"""
        rft = RegisterFileTestbench({
            'metadata': {'name': 'test'},
            'fields': [
                {
                    'address': 0,
                    'bitrange': '2..0',
                    'name': 'a',
                    'behavior': 'custom',
                    'interfaces': [
                        {'drive': 'a:3'},
                        {'strobe': 'b:3'},
                        {'state': 'data:3'},
                    ],
                    'write': (
                        '$s.data$ := $data$;\n'
                        '$ack$ := true;\n'
                        '$s.b$ := "111";\n'
                    ),
                    'post-access': (
                        '$s.a$ := $s.data$;\n'
                        'if reset = \'1\' then'
                        '  $s.data$ := "000";\n'
                        'end if;\n'
                    ),
                },
                {
                    'address': 4,
                    'bitrange': 0,
                    'repeat': 3,
                    'name': 'b',
                    'behavior': 'custom',
                    'interfaces': [
                        {'monitor': 'a'},
                        {'strobe': 'b'},
                    ],
                    'read': (
                        '$data$ := $s.a$;\n'
                        '$ack$ := true;\n'
                        '$s.b$ := \'1\';\n'
                    ),
                },
                {
                    'address': 8,
                    'name': 'c',
                    'behavior': 'custom',
                    'interfaces': [
                        {'monitor': 'b:3'},
                        {'state': 'count:32'},
                    ],
                    'pre-access': (
                        'if $s.b$(0) = \'1\' then'
                        '  $s.count$ := std_logic_vector(unsigned($s.count$) + 1);\n'
                        'end if;\n'
                    ),
                    'read': (
                        '$data$ := $s.count$;\n'
                        '$ack$ := true;\n'
                    ),
                    'post-access': (
                        'if reset = \'1\' then'
                        '  $s.count$ := (others => \'0\');\n'
                        'end if;\n'
                    ),
                },
            ]})
        self.assertEqual(rft.ports, (
            'bus',
        ))
        with rft as objs:
            self.assertEqual(objs.bus.read(8), 0)
            self.assertEqual(objs.bus.read(4), 0)
            self.assertEqual(objs.bus.read(8), 1)
            objs.bus.write(0, 3)
            self.assertEqual(objs.bus.read(8), 2)
            self.assertEqual(objs.bus.read(4), 3)
            self.assertEqual(objs.bus.read(8), 3)
            objs.bus.write(0, 4)
            self.assertEqual(objs.bus.read(8), 4)
            self.assertEqual(objs.bus.read(4), 4)
            self.assertEqual(objs.bus.read(8), 5)

    def test_errors(self):
        """test custom field errors"""
        msg = ('must support either or both read and write mode')
        with self.assertRaisesRegex(Exception, msg):
            RegisterFileTestbench({
                'metadata': {'name': 'test'},
                'fields': [
                    {
                        'address': 0,
                        'name': 'a',
                        'behavior': 'custom',
                    },
                ]})
