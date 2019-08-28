"""Primitive flag field tests."""

from unittest import TestCase
from ..testbench import RegisterFileTestbench

class TestPrimitiveFlagFields(TestCase):
    """Primitive flag field tests"""

    def test_normal(self):
        """test normal flag fields"""
        rft = RegisterFileTestbench({
            'metadata': {'name': 'test'},
            'fields': [
                {
                    'address': 0,
                    'name': 'a',
                    'behavior': 'flag',
                    'bit-overflow-internal': 'b',
                    'bit-underflow-internal': 'c',
                },
                {
                    'address': 4,
                    'bitrange': 0,
                    'name': 'b',
                    'behavior': 'internal-flag',
                    'internal': 'b',
                },
                {
                    'address': 4,
                    'bitrange': 1,
                    'name': 'c',
                    'behavior': 'internal-flag',
                    'internal': 'c',
                },
            ]})
        with rft as objs:
            self.assertEqual(objs.bus.read(0), 0)
            self.assertEqual(objs.bus.read(4), 0)
            objs.f_a_i.bit_set.val = 0x33
            rft.testbench.clock()
            objs.f_a_i.bit_set.val = 0x00
            self.assertEqual(objs.bus.read(0), 0x33)
            self.assertEqual(objs.bus.read(4), 0)
            objs.bus.write(0, 0x55)
            self.assertEqual(objs.bus.read(0), 0x22)
            self.assertEqual(objs.bus.read(4), 2)
            objs.bus.write(4, 3)
            self.assertEqual(objs.bus.read(4), 0)
            objs.f_a_i.bit_set.val = 0x0F
            rft.testbench.clock()
            objs.f_a_i.bit_set.val = 0x00
            self.assertEqual(objs.bus.read(0), 0x2F)
            self.assertEqual(objs.bus.read(4), 1)
            objs.bus.write(4, 3)
            self.assertEqual(objs.bus.read(4), 0)

    def test_volatile(self):
        """test volatile flag fields"""
        rft = RegisterFileTestbench({
            'metadata': {'name': 'test'},
            'fields': [
                {
                    'address': 0,
                    'name': 'a',
                    'behavior': 'volatile-flag',
                    'bit-overflow-internal': 'b',
                },
                {
                    'address': 4,
                    'bitrange': 0,
                    'name': 'b',
                    'behavior': 'volatile-internal-flag',
                    'internal': 'b',
                },
            ]})
        with rft as objs:
            self.assertEqual(objs.bus.read(0), 0)
            self.assertEqual(objs.bus.read(4), 0)
            objs.f_a_i.bit_set.val = 0x33
            rft.testbench.clock()
            objs.f_a_i.bit_set.val = 0x00
            self.assertEqual(objs.bus.read(0), 0x33)
            self.assertEqual(objs.bus.read(4), 0)
            self.assertEqual(objs.bus.read(0), 0x00)
            self.assertEqual(objs.bus.read(4), 0)
            objs.f_a_i.bit_set.val = 0x33
            rft.testbench.clock()
            objs.f_a_i.bit_set.val = 0x0F
            rft.testbench.clock()
            objs.f_a_i.bit_set.val = 0x00
            self.assertEqual(objs.bus.read(0), 0x3F)
            self.assertEqual(objs.bus.read(4), 1)
            self.assertEqual(objs.bus.read(0), 0x00)
            self.assertEqual(objs.bus.read(4), 0)
