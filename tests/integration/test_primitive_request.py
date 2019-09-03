"""Primitive request field tests."""

from unittest import TestCase
from ..testbench import RegisterFileTestbench

class TestPrimitiveRequestFields(TestCase):
    """Primitive request field tests"""

    def test_fields(self):
        """test request fields"""
        rft = RegisterFileTestbench({
            'metadata': {'name': 'test'},
            'fields': [
                {
                    'address': 0,
                    'bitrange': '30..0',
                    'name': 'ax',
                    'behavior': 'strobe',
                },
                {
                    'address': 0,
                    'bitrange': 31,
                    'name': 'ay',
                    'behavior': 'internal-strobe',
                    'internal': 'd',
                },
                {
                    'address': 4,
                    'name': 'b',
                    'behavior': 'request',
                    'bit-overflow-internal': 'e',
                    'bit-underflow-internal': 'f',
                },
                {
                    'address': 8,
                    'name': 'c',
                    'behavior': 'multi-request',
                    'overflow-internal': 'g',
                    'underflow-internal': 'h',
                },
                {
                    'address': 12,
                    'bitrange': 0,
                    'name': 'd',
                    'behavior': 'internal-flag',
                    'internal': 'd',
                },
                {
                    'address': 12,
                    'bitrange': 1,
                    'name': 'e',
                    'behavior': 'internal-flag',
                    'internal': 'e',
                },
                {
                    'address': 12,
                    'bitrange': 2,
                    'name': 'f',
                    'behavior': 'internal-flag',
                    'internal': 'f',
                },
                {
                    'address': 12,
                    'bitrange': 3,
                    'name': 'g',
                    'behavior': 'internal-flag',
                    'internal': 'g',
                },
                {
                    'address': 12,
                    'bitrange': 4,
                    'name': 'h',
                    'behavior': 'internal-flag',
                    'internal': 'h',
                },
                {
                    'address': 16,
                    'name': 'i',
                    'behavior': 'multi-request',
                    'ctrl-decrement': False,
                    'hw-write': 'subtract',
                    'overflow-internal': 'g',
                    'underflow-internal': 'h',
                },
            ]})
        self.assertEqual(rft.ports, (
            'bus',
            'f_ax_o.data',
            'f_b_i.bit_clear',
            'f_b_o.data',
            'f_c_i.decrement',
            'f_c_o.data',
            'f_i_i.write_data',
            'f_i_i.write_enable',
            'f_i_o.data',
        ))
        with rft as objs:
            resp = []
            def handle(code):
                resp.append(int(code))
            objs.bus.async_write(handle, 0, 42)
            for _ in range(10):
                rft.testbench.clock()
                if int(objs.f_ax_o.data):
                    break
            self.assertEqual(int(objs.f_ax_o.data), 42)
            rft.testbench.clock()
            self.assertEqual(int(objs.f_ax_o.data), 0)
            self.assertEqual(resp, [0])
            self.assertEqual(objs.bus.read(12), 0)
            objs.bus.write(0, 0x80000000)
            self.assertEqual(objs.bus.read(12), 1)
            objs.bus.write(12, 0xFF)
            with self.assertRaisesRegex(ValueError, 'decode'):
                objs.bus.read(0)

            self.assertEqual(objs.bus.read(4), 0x00)
            objs.bus.write(4, 0x33)
            self.assertEqual(objs.bus.read(4), 0x33)
            self.assertEqual(objs.bus.read(12), 0)
            objs.bus.write(4, 0x42)
            self.assertEqual(objs.bus.read(4), 0x73)
            self.assertEqual(objs.bus.read(12), 2)
            objs.bus.write(12, 0xFF)
            objs.f_b_i.bit_clear.val = 0x33
            rft.testbench.clock()
            objs.f_b_i.bit_clear.val = 0
            self.assertEqual(objs.bus.read(4), 0x40)
            self.assertEqual(objs.bus.read(12), 0)
            objs.f_b_i.bit_clear.val = 0x42
            rft.testbench.clock()
            objs.f_b_i.bit_clear.val = 0
            self.assertEqual(objs.bus.read(4), 0x0)
            self.assertEqual(objs.bus.read(12), 4)
            objs.bus.write(12, 0xFF)

            self.assertEqual(objs.bus.read(8), 0)
            objs.bus.write(8, 1)
            self.assertEqual(objs.bus.read(8), 1)
            self.assertEqual(objs.bus.read(12), 0)
            objs.bus.write(8, 4)
            self.assertEqual(objs.bus.read(8), 5)
            self.assertEqual(objs.bus.read(12), 0)
            objs.bus.write(8, 0xFFFFFFFF)
            self.assertEqual(objs.bus.read(8), 4)
            self.assertEqual(objs.bus.read(12), 8)
            objs.bus.write(12, 0xFF)
            objs.f_c_i.decrement.val = 1
            rft.testbench.clock(2)
            objs.f_c_i.decrement.val = 0
            self.assertEqual(objs.bus.read(8), 2)
            self.assertEqual(objs.bus.read(12), 0)
            objs.f_c_i.decrement.val = 1
            rft.testbench.clock(3)
            objs.f_c_i.decrement.val = 0
            self.assertEqual(objs.bus.read(8), 0xFFFFFFFF)
            self.assertEqual(objs.bus.read(12), 16)
            objs.bus.write(12, 0xFF)

            self.assertEqual(objs.bus.read(16), 0x00000000)
            objs.bus.write(16, 0x11223344)
            self.assertEqual(objs.bus.read(16), 0x11223344)
            self.assertEqual(objs.bus.read(12), 0)
            objs.bus.write(16, 0x88776655)
            self.assertEqual(objs.bus.read(16), 0x99999999)
            self.assertEqual(objs.bus.read(12), 0)
            objs.bus.write(16, 0xFFFFFFFF)
            self.assertEqual(objs.bus.read(16), 0x99999998)
            self.assertEqual(objs.bus.read(12), 8)
            objs.bus.write(12, 0xFF)
            objs.f_i_i.write_data.val = 0x88888888
            objs.f_i_i.write_enable.val = 1
            rft.testbench.clock()
            objs.f_i_i.write_data.val = 0
            self.assertEqual(objs.bus.read(16), 0x11111110)
            self.assertEqual(objs.bus.read(12), 0)
            objs.f_i_i.write_data.val = 0x11111111
            objs.f_i_i.write_enable.val = 1
            rft.testbench.clock()
            objs.f_i_i.write_data.val = 0
            self.assertEqual(objs.bus.read(16), 0xFFFFFFFF)
            self.assertEqual(objs.bus.read(12), 16)
            objs.bus.write(12, 0xFF)
