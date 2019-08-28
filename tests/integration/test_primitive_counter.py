"""Primitive counter field tests."""

from unittest import TestCase
from ..testbench import RegisterFileTestbench

class TestPrimitiveCounterFields(TestCase):
    """Primitive counter field tests"""

    def test_normal(self):
        """test normal counter fields"""
        rft = RegisterFileTestbench({
            'metadata': {'name': 'test'},
            'fields': [
                {
                    'address': 0,
                    'bitrange': '3..0',
                    'name': 'a',
                    'behavior': 'counter',
                    'overflow-internal': 'b',
                    'underflow-internal': 'c',
                },
                {
                    'address': 4,
                    'bitrange': '3..0',
                    'name': 'b',
                    'behavior': 'internal-counter',
                    'internal': 'b',
                },
                {
                    'address': 4,
                    'bitrange': '7..4',
                    'name': 'c',
                    'behavior': 'internal-counter',
                    'internal': 'c',
                },
            ]})
        with rft as objs:
            self.assertEqual(objs.bus.read(0), 0x00)
            self.assertEqual(objs.bus.read(4), 0x00)
            objs.f_a_i.increment.val = 1
            rft.testbench.clock(10)
            objs.f_a_i.increment.val = 0
            self.assertEqual(objs.bus.read(0), 10)
            self.assertEqual(objs.bus.read(4), 0x00)
            objs.bus.write(0, 5)
            self.assertEqual(objs.bus.read(0), 5)
            self.assertEqual(objs.bus.read(4), 0x00)
            objs.bus.write(0, 6)
            self.assertEqual(objs.bus.read(0), 15)
            self.assertEqual(objs.bus.read(4), 0x10)
            objs.f_a_i.increment.val = 1
            rft.testbench.clock(10)
            objs.f_a_i.increment.val = 0
            self.assertEqual(objs.bus.read(0), 9)
            self.assertEqual(objs.bus.read(4), 0x11)
            objs.f_a_i.increment.val = 1
            rft.testbench.clock(10)
            objs.f_a_i.increment.val = 0
            self.assertEqual(objs.bus.read(0), 3)
            self.assertEqual(objs.bus.read(4), 0x12)
            objs.bus.write(4, 0x11)
            self.assertEqual(objs.bus.read(4), 0x01)
            objs.bus.write(4, 0x11)
            self.assertEqual(objs.bus.read(4), 0xF0)

    def test_volatile(self):
        """test volatile counter fields"""
        rft = RegisterFileTestbench({
            'metadata': {'name': 'test'},
            'fields': [
                {
                    'address': 0,
                    'bitrange': '3..0',
                    'name': 'a',
                    'behavior': 'volatile-counter',
                    'overflow-internal': 'b',
                },
                {
                    'address': 4,
                    'bitrange': '3..0',
                    'name': 'b',
                    'behavior': 'volatile-internal-counter',
                    'internal': 'b',
                },
            ]})
        with rft as objs:
            self.assertEqual(objs.bus.read(0), 0x0)
            self.assertEqual(objs.bus.read(4), 0x0)
            objs.f_a_i.increment.val = 1
            rft.testbench.clock(10)
            objs.f_a_i.increment.val = 0
            self.assertEqual(objs.bus.read(0), 10)
            self.assertEqual(objs.bus.read(4), 0x0)
            self.assertEqual(objs.bus.read(0), 0x0)
            self.assertEqual(objs.bus.read(4), 0x0)
            objs.f_a_i.increment.val = 1
            rft.testbench.clock(0x42)
            objs.f_a_i.increment.val = 0
            self.assertEqual(objs.bus.read(0), 0x2)
            self.assertEqual(objs.bus.read(4), 0x4)
            self.assertEqual(objs.bus.read(0), 0x0)
            self.assertEqual(objs.bus.read(4), 0x0)
