"""Primitive constant field tests."""

from copy import deepcopy
from unittest import TestCase
from ..testbench import RegisterFileTestbench

class TestPrimitiveConstantFields(TestCase):
    """Primitive constant field tests"""

    def test_fields(self):
        """test constant fields"""
        rft = RegisterFileTestbench({
            'metadata': {'name': 'test'},
            'fields': [
                {
                    'address': 0,
                    'name': 'a',
                    'behavior': 'constant',
                    'value': 33,
                },
                {
                    'address': 4,
                    'name': 'b',
                    'behavior': 'config',
                },
            ]}, ('F_B_RESET_DATA', '"{:032b}"'.format(42)))
        with rft as objs:
            objs.bus.read(0, 33)
            with self.assertRaisesRegex(ValueError, 'decode'):
                objs.bus.write(0, 0)

            objs.bus.read(4, 42)
            with self.assertRaisesRegex(ValueError, 'decode'):
                objs.bus.write(4, 0)

    def test_errors(self):
        """test constant field config errors"""
        msg = ('requires key value to be defined')
        with self.assertRaisesRegex(Exception, msg):
            RegisterFileTestbench({
                'metadata': {'name': 'test'},
                'fields': [
                    {
                        'address': 0,
                        'name': 'a',
                        'behavior': 'constant',
                    },
                ]})
