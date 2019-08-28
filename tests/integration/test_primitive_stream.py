"""Primitive stream field tests."""

from unittest import TestCase
from ..testbench import RegisterFileTestbench

class TestPrimitiveStreamFields(TestCase):
    """Primitive stream field tests"""

    def test_stream_to_mmio(self):
        """test stream to MMIO field"""
        rft = RegisterFileTestbench({
            'metadata': {'name': 'test'},
            'fields': [
                {
                    'address': 0,
                    'name': 'a',
                    'behavior': 'stream-to-mmio',
                    'full-internal': 'a_full',
                    'empty-internal': 'a_empty',
                    'underrun-internal': 'a_under',
                },
                {
                    'address': 4,
                    'name': 'b',
                    'behavior': 'stream-to-mmio',
                    'bus-read': 'valid-only',
                    'full-internal': 'b_full',
                    'empty-internal': 'b_empty',
                    'reset': 33,
                },
                {
                    'address': 8,
                    'bitrange': 0,
                    'name': 'a_full',
                    'behavior': 'internal-status',
                    'internal': 'a_full',
                },
                {
                    'address': 8,
                    'bitrange': 1,
                    'name': 'a_empty',
                    'behavior': 'internal-status',
                    'internal': 'a_empty',
                },
                {
                    'address': 8,
                    'bitrange': 2,
                    'name': 'a_under',
                    'behavior': 'internal-flag',
                    'internal': 'a_under',
                },
                {
                    'address': 8,
                    'bitrange': 3,
                    'name': 'b_full',
                    'behavior': 'internal-status',
                    'internal': 'b_full',
                },
                {
                    'address': 8,
                    'bitrange': 4,
                    'name': 'b_empty',
                    'behavior': 'internal-status',
                    'internal': 'b_empty',
                },
            ]})
        with rft as objs:
            rft.testbench.clock()
            self.assertEqual(objs.bus.read(8), 0b01010)
            self.assertEqual(objs.bus.read(0), 0)
            self.assertEqual(objs.bus.read(8), 0b01110)
            objs.bus.write(8, 0b00100)
            objs.f_a_i.data.val = 33
            objs.f_a_i.valid.val = 1
            rft.testbench.clock() # needed because the test case runner is synchronous
            objs.f_a_i.valid.val = 0
            self.assertEqual(int(objs.f_a_o.ready), 1)
            rft.testbench.clock()
            self.assertEqual(int(objs.f_a_o.ready), 0)
            self.assertEqual(objs.bus.read(8), 0b01001)
            self.assertEqual(objs.bus.read(0), 33)
            self.assertEqual(int(objs.f_a_o.ready), 1)
            self.assertEqual(objs.bus.read(8), 0b01010)
            self.assertEqual(objs.bus.read(0), 0)
            self.assertEqual(objs.bus.read(8), 0b01110)
            objs.bus.write(8, 0b00100)
            with self.assertRaisesRegex(ValueError, 'decode'):
                objs.bus.write(0, 0)

            self.assertEqual(objs.bus.read(4), 33)
            self.assertEqual(objs.bus.read(8), 0b10010)
            with self.assertRaisesRegex(ValueError, 'slave'):
                objs.bus.read(4)
            self.assertEqual(objs.bus.read(8), 0b10010)
            objs.f_b_i.data.val = 42
            objs.f_b_i.valid.val = 1
            rft.testbench.clock() # needed because the test case runner is synchronous
            objs.f_b_i.valid.val = 0
            self.assertEqual(int(objs.f_b_o.ready), 1)
            rft.testbench.clock()
            self.assertEqual(int(objs.f_b_o.ready), 0)
            self.assertEqual(objs.bus.read(8), 0b01010)
            self.assertEqual(objs.bus.read(4), 42)
            self.assertEqual(objs.bus.read(8), 0b10010)
            with self.assertRaisesRegex(ValueError, 'slave'):
                objs.bus.read(4)
            self.assertEqual(objs.bus.read(8), 0b10010)
            with self.assertRaisesRegex(ValueError, 'decode'):
                objs.bus.write(4, 0)

    def test_mmio_to_stream(self):
        """test MMIO to stream field"""
        rft = RegisterFileTestbench({
            'metadata': {'name': 'test'},
            'fields': [
                {
                    'address': 0,
                    'name': 'a',
                    'behavior': 'mmio-to-stream',
                    'full-internal': 'a_full',
                    'empty-internal': 'a_empty',
                    'overrun-internal': 'a_over',
                },
                {
                    'address': 4,
                    'name': 'b',
                    'behavior': 'mmio-to-stream',
                    'bus-write': 'invalid-only',
                    'full-internal': 'b_full',
                    'empty-internal': 'b_empty',
                    'reset': 33,
                },
                {
                    'address': 8,
                    'bitrange': 0,
                    'name': 'a_full',
                    'behavior': 'internal-status',
                    'internal': 'a_full',
                },
                {
                    'address': 8,
                    'bitrange': 1,
                    'name': 'a_empty',
                    'behavior': 'internal-status',
                    'internal': 'a_empty',
                },
                {
                    'address': 8,
                    'bitrange': 2,
                    'name': 'a_over',
                    'behavior': 'internal-flag',
                    'internal': 'a_over',
                },
                {
                    'address': 8,
                    'bitrange': 3,
                    'name': 'b_full',
                    'behavior': 'internal-status',
                    'internal': 'b_full',
                },
                {
                    'address': 8,
                    'bitrange': 4,
                    'name': 'b_empty',
                    'behavior': 'internal-status',
                    'internal': 'b_empty',
                },
            ]})
        with rft as objs:
            rft.testbench.clock()
            self.assertEqual(objs.bus.read(8), 0b01010)
            self.assertEqual(int(objs.f_a_o.data), 0)
            self.assertEqual(int(objs.f_a_o.valid), 0)
            objs.bus.write(0, 33)
            self.assertEqual(objs.bus.read(8), 0b01001)
            self.assertEqual(int(objs.f_a_o.data), 33)
            self.assertEqual(int(objs.f_a_o.valid), 1)
            objs.bus.write(0, 42) # ignored!
            self.assertEqual(objs.bus.read(8), 0b01101)
            objs.bus.write(8, 0b00100)
            self.assertEqual(int(objs.f_a_o.data), 33)
            self.assertEqual(int(objs.f_a_o.valid), 1)
            objs.f_a_i.ready.val = 1
            rft.testbench.clock()
            objs.f_a_i.ready.val = 0
            rft.testbench.clock() # needed because the test case runner is synchronous
            self.assertEqual(int(objs.f_a_o.valid), 0)
            self.assertEqual(objs.bus.read(8), 0b01010)
            with self.assertRaisesRegex(ValueError, 'decode'):
                objs.bus.read(0)

            self.assertEqual(int(objs.f_b_o.data), 33)
            self.assertEqual(int(objs.f_b_o.valid), 1)
            objs.f_b_i.ready.val = 1
            rft.testbench.clock()
            objs.f_b_i.ready.val = 0
            rft.testbench.clock() # needed because the test case runner is synchronous
            self.assertEqual(int(objs.f_b_o.valid), 0)
            self.assertEqual(objs.bus.read(8), 0b10010)
            objs.bus.write(4, 42)
            self.assertEqual(objs.bus.read(8), 0b01010)
            self.assertEqual(int(objs.f_b_o.data), 42)
            self.assertEqual(int(objs.f_b_o.valid), 1)
            with self.assertRaisesRegex(ValueError, 'slave'):
                objs.bus.write(4, 33)
            self.assertEqual(int(objs.f_b_o.data), 42)
            self.assertEqual(int(objs.f_b_o.valid), 1)
            with self.assertRaisesRegex(ValueError, 'decode'):
                objs.bus.read(4)
