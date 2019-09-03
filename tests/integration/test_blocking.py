"""Test blocking fields."""

from unittest import TestCase
from ..testbench import RegisterFileTestbench

class TestBlocking(TestCase):
    """Test blocking fields."""

    def test_block_normal(self):
        """test blocking + normal field"""
        rft = RegisterFileTestbench({
            'metadata': {'name': 'test'},
            'fields': [
                {
                    'address': 0,
                    'bitrange': '15..0',
                    'name': 'a',
                    'behavior': 'custom',
                    'interfaces': [{'state': 'count:4'}],
                    'read-can-block': True,
                    'read': (
                        'if $s.count$ = "1111" then\n'
                        '  $ack$ := true;\n'
                        '  $data$ := X"5678";\n'
                        'else\n'
                        '  $block$ := true;\n'
                        'end if;\n'
                        '$s.count$ := std_logic_vector(unsigned($s.count$) + 1);\n'
                    )
                },
                {
                    'address': 0,
                    'bitrange': '31..16',
                    'name': 'b',
                    'behavior': 'constant',
                    'value': 0x1234,
                }
            ]})
        self.assertEqual(rft.ports, ('bus',))
        with rft as objs:
            start = rft.testbench.cycle
            self.assertEqual(objs.bus.read(0), 0x12345678)
            self.assertEqual(rft.testbench.cycle - start, 17)

    def test_block_error(self):
        """test blocking + error field"""
        rft = RegisterFileTestbench({
            'metadata': {'name': 'test'},
            'fields': [
                {
                    'address': 0,
                    'bitrange': '15..0',
                    'name': 'a',
                    'behavior': 'custom',
                    'interfaces': [{'state': 'count:4'}],
                    'read-can-block': True,
                    'read': (
                        'if $s.count$ = "1111" then\n'
                        '  $ack$ := true;\n'
                        '  $data$ := X"5678";\n'
                        'else\n'
                        '  $block$ := true;\n'
                        'end if;\n'
                        '$s.count$ := std_logic_vector(unsigned($s.count$) + 1);\n'
                    )
                },
                {
                    'address': 0,
                    'bitrange': '31..16',
                    'name': 'b',
                    'behavior': 'primitive',
                    'bus-read': 'error',
                }
            ]})
        self.assertEqual(rft.ports, ('bus',))
        with rft as objs:
            start = rft.testbench.cycle
            with self.assertRaisesRegex(ValueError, 'slave'):
                objs.bus.read(0)
            self.assertEqual(rft.testbench.cycle - start, 17)

    def test_block_block(self):
        """test blocking + blocking field"""
        msg = (r'cannot have more than one blocking field in a '
               r'single register \(`A0` and `A1`\)')
        with self.assertRaisesRegex(Exception, msg):
            RegisterFileTestbench({
                'metadata': {'name': 'test'},
                'fields': [
                    {
                        'address': 0,
                        'bitrange': '15..0',
                        'repeat': 2,
                        'name': 'a',
                        'behavior': 'custom',
                        'interfaces': [{'state': 'count:4'}],
                        'read-can-block': True,
                        'read': (
                            'if $s.count$ = "1111" then\n'
                            '  $ack$ := true;\n'
                            '  $data$ := X"5678";\n'
                            'else\n'
                            '  $block$ := true;\n'
                            'end if;\n'
                            '$s.count$ := std_logic_vector(unsigned($s.count$) + 1);\n'
                        )
                    },
                ]})

    def test_block_volatile(self):
        """test blocking + volatile field"""
        msg = (r'cannot have both volatile fields \(`B`\) and blocking '
               r'fields \(`A`\) in a single register')
        with self.assertRaisesRegex(Exception, msg):
            RegisterFileTestbench({
                'metadata': {'name': 'test'},
                'fields': [
                    {
                        'address': 0,
                        'bitrange': '15..0',
                        'name': 'a',
                        'behavior': 'custom',
                        'interfaces': [{'state': 'count:4'}],
                        'read-can-block': True,
                        'read': (
                            'if $s.count$ = "1111" then\n'
                            '  $ack$ := true;\n'
                            '  $data$ := X"5678";\n'
                            'else\n'
                            '  $block$ := true;\n'
                            'end if;\n'
                            '$s.count$ := std_logic_vector(unsigned($s.count$) + 1);\n'
                        )
                    },
                    {
                        'address': 0,
                        'bitrange': '31..16',
                        'name': 'b',
                        'behavior': 'primitive',
                        'bus-read': 'enabled',
                        'after-bus-read': 'increment',
                    }
                ]})
