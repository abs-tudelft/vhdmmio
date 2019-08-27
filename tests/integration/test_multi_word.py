"""Test multi-word registers."""

from unittest import TestCase
from ..testbench import RegisterFileTestbench

class TestMultiWord(TestCase):
    """Multi-word feature tests"""

    def test_multi_word(self):
        """test simple multi-word registers"""
        rft = RegisterFileTestbench({
            'metadata': {'name': 'test'},
            'fields': [
                {
                    'address': 0,
                    'bitrange': '31..0',
                    'name': 'xa',
                    'behavior': 'internal-control',
                    'internal': 'x',
                    'endianness': 'little',
                },
                {
                    'address': 0,
                    'bitrange': '63..32',
                    'name': 'ya',
                    'behavior': 'internal-control',
                    'internal': 'y',
                    'endianness': 'little',
                },
                {
                    'address': '0b10-00',
                    'bitrange': '31..0',
                    'name': 'xb',
                    'behavior': 'internal-status',
                    'internal': 'x',
                    'endianness': 'big',
                },
                {
                    'address': '0b10-00',
                    'bitrange': '63..32',
                    'name': 'yb',
                    'behavior': 'internal-status',
                    'internal': 'y',
                    'endianness': 'big',
                },
                {
                    'address': 8,
                    'name': 'xc',
                    'behavior': 'internal-status',
                    'internal': 'x',
                },
                {
                    'address': 12,
                    'name': 'yc',
                    'behavior': 'internal-status',
                    'internal': 'y',
                },
            ]})
        with rft as objs:
            objs.bus.write(0, 0x11223344)
            objs.bus.write(4, 0x55667788)
            self.assertEqual(objs.bus.read(16), 0x55667788)
            self.assertEqual(objs.bus.read(24), 0x11223344)
            self.assertEqual(objs.bus.read(20), 0x55667788)
            self.assertEqual(objs.bus.read(28), 0x11223344)
            self.assertEqual(objs.bus.read(8), 0x11223344)
            self.assertEqual(objs.bus.read(12), 0x55667788)

            # Test write atomicity.
            objs.bus.write(0, 0x22334455)
            self.assertEqual(objs.bus.read(8), 0x11223344)
            self.assertEqual(objs.bus.read(12), 0x55667788)
            objs.bus.write(4, 0x66778899)
            self.assertEqual(objs.bus.read(8), 0x22334455)
            self.assertEqual(objs.bus.read(12), 0x66778899)

            # Test read atomicity.
            self.assertEqual(objs.bus.read(16), 0x66778899)
            objs.bus.write(0, 0x11223344)
            objs.bus.write(4, 0x55667788)
            self.assertEqual(objs.bus.read(24), 0x22334455)
            self.assertEqual(objs.bus.read(16), 0x55667788)
            self.assertEqual(objs.bus.read(24), 0x11223344)

    def test_multi_word_error(self):
        """test errors related to multi-word registers"""
        msg = ('address conflict between block "x_reg_high" and field '
               '"y" at 0x00000004/2 in read mode')
        with self.assertRaisesRegex(Exception, msg):
            RegisterFileTestbench({
                'metadata': {'name': 'test'},
                'fields': [
                    {
                        'address': 0,
                        'bitrange': '63..0',
                        'name': 'x',
                        'behavior': 'control',
                    },
                    {
                        'address': 4,
                        'bitrange': '63..0',
                        'name': 'y',
                        'behavior': 'control',
                    },
                ]})

        msg = ('conflicting endianness specification')
        with self.assertRaisesRegex(Exception, msg):
            RegisterFileTestbench({
                'metadata': {'name': 'test'},
                'fields': [
                    {
                        'address': 0,
                        'bitrange': '31..0',
                        'name': 'xa',
                        'behavior': 'control',
                        'endianness': 'little',
                    },
                    {
                        'address': 0,
                        'bitrange': '63..32',
                        'name': 'ya',
                        'behavior': 'control',
                        'endianness': 'big',
                    },
                ]})

        RegisterFileTestbench({
            'metadata': {'name': 'test'},
            'features': {'endianness': 'big'},
            'fields': [
                {
                    'address': 0,
                    'bitrange': '31..0',
                    'name': 'xa',
                    'behavior': 'control',
                    'endianness': 'little',
                },
                {
                    'address': 0,
                    'bitrange': '63..32',
                    'name': 'ya',
                    'behavior': 'control',
                },
            ]})
