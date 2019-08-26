"""Test addressing features."""

from unittest import TestCase
from ..testbench import RegisterFileTestbench

class TestAddressing(TestCase):
    """Addressing feature tests"""

    def test_address_ok(self):
        """test correct address specifications"""
        rft = RegisterFileTestbench({
            'metadata': {'name': 'test'},
            'fields': [
                {
                    'address': 0,
                    'name': 'x',
                    'behavior': 'constant',
                    'value': 42
                },
                {
                    'address': '4',
                    'name': 'y',
                    'behavior': 'constant',
                    'value': 33
                },
                {
                    'address': '0x1-',
                    'name': 'a',
                    'behavior': 'constant',
                    'value': 4
                },
                {
                    'address': '0x[001-]-',
                    'name': 'b',
                    'behavior': 'constant',
                    'value': 8
                },
                {
                    'address': '0b1------',
                    'name': 'c',
                    'behavior': 'constant',
                    'value': 15
                },
                {
                    'address': '0x80/7',
                    'name': 'd',
                    'behavior': 'constant',
                    'value': 16
                },
                {
                    'address': '0x100|0xFF',
                    'name': 'e',
                    'behavior': 'constant',
                    'value': 23
                },
                {
                    'address': '0x200&0xE00',
                    'name': 'f',
                    'behavior': 'constant',
                    'value': 42
                },
            ]})
        with rft as objs:
            for addr in range(4):
                self.assertEqual(objs.bus.read(addr), 42)
            for addr in range(4, 8):
                self.assertEqual(objs.bus.read(addr), 33)
            with self.assertRaisesRegex(ValueError, 'decode'):
                objs.bus.read(8)
            with self.assertRaisesRegex(ValueError, 'decode'):
                objs.bus.read(12)
            magic = [4, 8, 15, 16, 23, 42, None]
            for bit_a in range(7):
                for bit_b in range(7):
                    if bit_a == bit_b:
                        continue
                    exp = magic[max(bit_a, bit_b)]
                    addr = (16 << bit_a) | (16 << bit_b)
                    if exp is None:
                        with self.assertRaisesRegex(ValueError, 'decode'):
                            objs.bus.read(addr)
                    else:
                        self.assertEqual(objs.bus.read(addr), exp)

    def test_address_error(self):
        """test erroneous address specifications"""
        msg = (r'address conflict between field "y" \(0x00000008/3\) and field '
               r'"x" \(0b0000000000000000000000000000-1--\) at 0x0000000C in '
               r'read mode')
        with self.assertRaisesRegex(Exception, msg):
            RegisterFileTestbench({
                'metadata': {'name': 'test'},
                'fields': [
                    {
                        'address': '0b-1--',
                        'name': 'x',
                        'behavior': 'constant',
                        'value': 42
                    },
                    {
                        'address': '0b1---',
                        'name': 'y',
                        'behavior': 'constant',
                        'value': 33
                    },
                ]})


        msg = (r'fields\[0\].address must be an integer above or equal to 0, a '
               r'hex/bin integer with don\'t cares, `<address>/<size>`, '
               r'`<address>\|<ignore>`, or `<address>\&<mask>`, but was `-4`')
        with self.assertRaisesRegex(Exception, msg):
            RegisterFileTestbench({
                'metadata': {'name': 'test'},
                'fields': [
                    {
                        'address': -4,
                        'name': 'x',
                        'behavior': 'constant',
                        'value': 42
                    },
                ]})

        msg = (r'address 0xFFFFFFFFF is out of range for 32 bits')
        with self.assertRaisesRegex(Exception, msg):
            RegisterFileTestbench({
                'metadata': {'name': 'test'},
                'fields': [
                    {
                        'address': 0xFFFFFFFFF,
                        'name': 'x',
                        'behavior': 'constant',
                        'value': 42
                    },
                ]})

    def test_conditions(self):
        """test address specification with conditions"""
        magic = [4, 8, 15, 16, 23, 42]
        fields = []
        for idx, val in enumerate(magic):
            fields.append({
                'address': 0,
                'conditions': [
                    {
                        'internal': 'x:2',
                        'value': idx & 3
                    },
                    {
                        'internal': 'y',
                        'value': idx >> 2
                    },
                ],
                'name': chr(ord('a') + idx),
                'behavior': 'constant',
                'value': val,
            })

        fields.append({
            'address': 4,
            'bitrange': '1..0',
            'name': 'x',
            'behavior': 'internal-control',
            'internal': 'x',
        })

        fields.append({
            'address': 4,
            'bitrange': 2,
            'name': 'y',
            'behavior': 'internal-control',
            'internal': 'y',
        })

        rft = RegisterFileTestbench({
            'metadata': {'name': 'test'},
            'fields': fields,
        })
        with rft as objs:
            for idx, val in enumerate(magic):
                objs.bus.write(4, idx)
                self.assertEqual(objs.bus.read(0), val)

            objs.bus.write(4, 7)
            with self.assertRaisesRegex(ValueError, 'decode'):
                objs.bus.read(0)
