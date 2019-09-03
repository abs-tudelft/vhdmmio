"""Primitive control field tests."""

from unittest import TestCase
from ..testbench import RegisterFileTestbench

class TestPrimitiveControlFields(TestCase):
    """Primitive control field tests"""

    def test_fields(self):
        """test control fields"""
        rft = RegisterFileTestbench({
            'metadata': {'name': 'test'},
            'fields': [
                {
                    'address': 0,
                    'name': 'a',
                    'behavior': 'control',
                },
                {
                    'address': 4,
                    'name': 'b',
                    'behavior': 'control',
                    'bus-write': 'enabled',
                    'ctrl-reset': True,
                    'reset': 33,
                },
                {
                    'address': 8,
                    'name': 'c',
                    'behavior': 'control',
                    'bus-write': 'invalid',
                    'after-bus-write': 'validate',
                    'hw-read': 'enabled',
                    'ctrl-lock': True,
                },
                {
                    'address': 12,
                    'name': 'd',
                    'behavior': 'control',
                    'bus-write': 'invalid-only',
                    'after-bus-write': 'validate',
                    'hw-read': 'enabled',
                    'ctrl-invalidate': True,
                },
                {
                    'address': 16,
                    'name': 'e',
                    'behavior': 'internal-control',
                    'internal': 'e',
                },
            ],
            'internal-io': [
                {
                    'internal': 'e:32',
                    'direction': 'output',
                },
            ]})
        self.assertEqual(rft.ports, (
            'bus',
            'f_a_o.data',
            'f_b_i.reset',
            'f_b_o.data',
            'f_c_i.lock',
            'f_c_o.data',
            'f_c_o.valid',
            'f_d_i.invalidate',
            'f_d_o.data',
            'f_d_o.valid',
            's_e'
        ))
        with rft as objs:
            self.assertEqual(objs.bus.read(0), 0)
            self.assertEqual(int(objs.f_a_o.data), 0)
            objs.bus.write(0, 0x11223344)
            self.assertEqual(objs.bus.read(0), 0x11223344)
            self.assertEqual(int(objs.f_a_o.data), 0x11223344)
            objs.bus.write(0, 0x55667788, '0101')
            self.assertEqual(objs.bus.read(0), 0x11663388)
            self.assertEqual(int(objs.f_a_o.data), 0x11663388)

            self.assertEqual(objs.bus.read(4), 33)
            self.assertEqual(int(objs.f_b_o.data), 33)
            objs.bus.write(4, 0x11223344)
            self.assertEqual(objs.bus.read(4), 0x11223344)
            self.assertEqual(int(objs.f_b_o.data), 0x11223344)
            objs.bus.write(4, 0x55667788, '0101')
            self.assertEqual(objs.bus.read(4), 0x00660088)
            self.assertEqual(int(objs.f_b_o.data), 0x00660088)
            objs.f_b_i.reset.val = 1
            rft.testbench.clock()
            objs.f_b_i.reset.val = 0
            self.assertEqual(objs.bus.read(4), 33)
            self.assertEqual(int(objs.f_b_o.data), 33)

            self.assertEqual(objs.bus.read(8), 0)
            self.assertEqual(int(objs.f_c_o.data), 0)
            self.assertEqual(int(objs.f_c_o.valid), 0)
            objs.f_c_i.lock.val = 1
            with self.assertRaisesRegex(ValueError, 'decode'):
                objs.bus.write(8, 33)
            self.assertEqual(objs.bus.read(8), 0)
            self.assertEqual(int(objs.f_c_o.data), 0)
            self.assertEqual(int(objs.f_c_o.valid), 0)
            objs.f_c_i.lock.val = 0
            objs.bus.write(8, 42)
            self.assertEqual(objs.bus.read(8), 42)
            self.assertEqual(int(objs.f_c_o.data), 42)
            self.assertEqual(int(objs.f_c_o.valid), 1)
            objs.bus.write(8, 55)
            self.assertEqual(objs.bus.read(8), 42)
            self.assertEqual(int(objs.f_c_o.data), 42)
            self.assertEqual(int(objs.f_c_o.valid), 1)

            self.assertEqual(objs.bus.read(12), 0)
            self.assertEqual(int(objs.f_d_o.data), 0)
            self.assertEqual(int(objs.f_d_o.valid), 0)
            objs.bus.write(12, 33)
            self.assertEqual(objs.bus.read(12), 33)
            self.assertEqual(int(objs.f_d_o.data), 33)
            self.assertEqual(int(objs.f_d_o.valid), 1)
            with self.assertRaisesRegex(ValueError, 'slave'):
                objs.bus.write(12, 55)
            self.assertEqual(objs.bus.read(12), 33)
            self.assertEqual(int(objs.f_d_o.data), 33)
            self.assertEqual(int(objs.f_d_o.valid), 1)
            objs.f_d_i.invalidate.val = 1
            rft.testbench.clock()
            objs.f_d_i.invalidate.val = 0
            objs.bus.write(12, 55)
            with self.assertRaisesRegex(ValueError, 'slave'):
                objs.bus.write(12, 42)
            self.assertEqual(objs.bus.read(12), 55)
            self.assertEqual(int(objs.f_d_o.data), 55)
            self.assertEqual(int(objs.f_d_o.valid), 1)

            self.assertEqual(objs.bus.read(16), 0)
            self.assertEqual(int(objs.s_e), 0)
            objs.bus.write(16, 33)
            self.assertEqual(objs.bus.read(16), 33)
            self.assertEqual(int(objs.s_e), 33)
