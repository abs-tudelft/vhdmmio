"""Primitive status field tests."""

from unittest import TestCase
from ..testbench import RegisterFileTestbench

class TestPrimitiveStatusFields(TestCase):
    """Primitive status field tests"""

    def test_fields(self):
        """test status fields"""
        rft = RegisterFileTestbench({
            'metadata': {'name': 'test'},
            'fields': [
                {
                    'address': 0,
                    'name': 'a',
                    'behavior': 'status',
                },
                {
                    'address': 4,
                    'name': 'b',
                    'behavior': 'internal-status',
                    'internal': 'b',
                },
                {
                    'address': 8,
                    'name': 'c',
                    'behavior': 'latching',
                },
                {
                    'address': 12,
                    'name': 'd',
                    'behavior': 'latching',
                    'bus-read': 'valid-wait',
                    'ctrl-validate': True,
                },
                {
                    'address': 16,
                    'name': 'e',
                    'behavior': 'latching',
                    'bus-read': 'valid-only',
                    'after-bus-read': 'invalidate',
                    'after-hw-write': 'validate',
                    'reset': 33,
                },
            ],
            'internal-io': [
                {
                    'internal': 'b:32',
                    'direction': 'input',
                },
            ]})
        #rft.testbench.with_gui()
        with rft as objs:
            objs.f_a_i.write_data.val = 33
            self.assertEqual(objs.bus.read(0), 33)
            objs.f_a_i.write_data.val = 42
            self.assertEqual(objs.bus.read(0), 42)
            with self.assertRaisesRegex(ValueError, 'decode'):
                objs.bus.write(0, 0)

            objs.s_b.val = 33
            self.assertEqual(objs.bus.read(4), 33)
            objs.s_b.val = 42
            self.assertEqual(objs.bus.read(4), 42)
            with self.assertRaisesRegex(ValueError, 'decode'):
                objs.bus.write(4, 0)

            self.assertEqual(objs.bus.read(8), 0)
            objs.f_c_i.write_data.val = 33
            self.assertEqual(objs.bus.read(8), 0)
            objs.f_c_i.write_enable.val = 1
            self.assertEqual(objs.bus.read(8), 33)
            objs.f_c_i.write_enable.val = 0
            objs.f_c_i.write_data.val = 42
            self.assertEqual(objs.bus.read(8), 33)
            self.assertEqual(objs.bus.read(8), 33)
            with self.assertRaisesRegex(ValueError, 'decode'):
                objs.bus.write(8, 0)

            res = []
            def result(data, resp):
                res.append((int(data), int(resp)))
            objs.bus.async_read(result, 12)
            objs.bus.async_read(result, 12)
            rft.testbench.clock(20)
            self.assertEqual(res, [])
            objs.f_d_i.write_data.val = 33
            objs.f_d_i.write_enable.val = 1
            rft.testbench.clock(1)
            objs.f_d_i.write_enable.val = 0
            rft.testbench.clock(20)
            self.assertEqual(res, [])
            objs.f_d_i.validate.val = 1
            rft.testbench.clock(1)
            objs.f_d_i.validate.val = 0
            rft.testbench.clock(10)
            self.assertEqual(res, [(33, 0), (33, 0)])
            with self.assertRaisesRegex(ValueError, 'decode'):
                objs.bus.write(12, 0)

            self.assertEqual(objs.bus.read(16), 33)
            with self.assertRaisesRegex(ValueError, 'slave'):
                objs.bus.read(16)
            objs.f_e_i.write_data.val = 42
            objs.f_e_i.write_enable.val = 1
            rft.testbench.clock(1)
            objs.f_e_i.write_enable.val = 0
            rft.testbench.clock(10)
            self.assertEqual(objs.bus.read(16), 42)
            with self.assertRaisesRegex(ValueError, 'slave'):
                objs.bus.read(16)
