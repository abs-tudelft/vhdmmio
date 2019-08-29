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
        #rft.testbench.with_gui()
        with rft as objs:
            self.assertEqual(objs.bus.read(0), 0x11223344)
            with self.assertRaisesRegex(ValueError, 'decode'):
                objs.bus.write(0, 0)

            objs.bus.write(4, 0x11223344)
            with self.assertRaisesRegex(ValueError, 'slave'):
                objs.bus.write(4, 0x44332211)
            with self.assertRaisesRegex(ValueError, 'decode'):
                objs.bus.read(4)

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
