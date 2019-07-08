"""Tests for primitive fields and derivatives."""

from unittest import TestCase
from .testbench import RegisterFileTestbench

class TestPrimitive(TestCase):
    """Tests for primitive fields and derivatives."""

    def test_control(self):
        """test control fields"""
        rft = RegisterFileTestbench({
            'meta': {'name': 'test'},
            'features': {'bus-width': 32, 'optimize': True},
            'fields': [
                {
                    'address': '0x00:3..0',
                    'register-name': 'a',
                    'name': 'a',
                    'type': 'control',
                },
                {
                    'address': '0x00:4',
                    'name': 'b',
                    'type': 'control',
                    'repeat': 3,
                },
                {
                    'address': '0x04',
                    'name': 'c',
                    'type': 'control',
                },
            ]
        })
        with rft as objs:

            # Test reset value and a basic 4-bit field.
            self.assertEqual(int(objs.f_a_o.data), 0)
            self.assertEqual(objs.bus.read(0), 0)
            objs.bus.write(0, 3)
            self.assertEqual(int(objs.f_a_o.data), 3)
            self.assertEqual(objs.bus.read(0), 3)

            # Test masked write access.
            self.assertEqual(int(objs.f_c_o.data), 0)
            objs.bus.write(4, 0xDEADBEEF)
            self.assertEqual(int(objs.f_a_o.data), 3)
            self.assertEqual(int(objs.f_c_o.data), 0xDEADBEEF)
            objs.bus.write(4, 0x33333333, 2)
            self.assertEqual(int(objs.f_c_o.data), 0xDEAD33EF)
            self.assertEqual(objs.bus.read(4), 0xDEAD33EF)

            # Test an array of std_logic fields.
            for i in range(3):
                self.assertEqual(int(objs.f_b_o[i].data), 0)
            objs.bus.write(0, 0x30)
            self.assertEqual(int(objs.f_b_o[0].data), 1)
            self.assertEqual(int(objs.f_b_o[1].data), 1)
            self.assertEqual(int(objs.f_b_o[2].data), 0)
