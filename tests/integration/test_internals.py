"""Tests for internal signals."""

from unittest import TestCase
from ..testbench import RegisterFileTestbench

class TestInternals(TestCase):
    """Tests for internal signals"""

    def test_internals_1(self):
        """test driven internals connected to fields"""
        rft = RegisterFileTestbench({
            'metadata': {'name': 'test'},
            'fields': [
                {
                    'address': '0',
                    'bitrange': 0,
                    'name': 'a',
                    'behavior': 'internal-control',
                    'internal': 'x',
                },
                {
                    'address': '0',
                    'bitrange': '15..8',
                    'name': 'b',
                    'behavior': 'internal-control',
                    'internal': 'y',
                },
                {
                    'address': '4',
                    'bitrange': 1,
                    'name': 'c',
                    'behavior': 'internal-status',
                    'internal': 'x',
                },
                {
                    'address': '4',
                    'bitrange': '15..8',
                    'name': 'd',
                    'behavior': 'internal-status',
                    'internal': 'y',
                },
            ]})
        self.assertEqual(rft.ports, ('bus',))
        with rft as objs:
            self.assertEqual(objs.bus.read(0), 0)
            self.assertEqual(objs.bus.read(4), 0)
            objs.bus.write(0, 0xFFFF)
            self.assertEqual(objs.bus.read(0), 0xFF01)
            self.assertEqual(objs.bus.read(4), 0xFF02)
            objs.bus.write(0, 0x3300)
            self.assertEqual(objs.bus.read(0), 0x3300)
            self.assertEqual(objs.bus.read(4), 0x3300)

    def test_internals_2(self):
        """test driven internals connected to ports"""
        rft = RegisterFileTestbench({
            'metadata': {'name': 'test'},
            'internal-io': [
                {
                    'direction': 'input',
                    'internal': 'x',
                    'port': 'xi',
                },
                {
                    'direction': 'output',
                    'internal': 'x',
                    'port': 'xo',
                },
                {
                    'direction': 'input',
                    'internal': 'y:8',
                    'port': 'yi',
                },
                {
                    'direction': 'output',
                    'internal': 'y:8',
                    'port': 'yo',
                },
            ]})
        self.assertEqual(rft.ports, (
            'bus',
            's_xi',
            's_xo',
            's_yi',
            's_yo',
        ))
        with rft as objs:
            # Note: latency is two cycles; one for the entity itself, and one
            # for the testbench.
            objs.s_xi.val = 0
            objs.s_yi.val = 0
            rft.testbench.clock()
            objs.s_xi.val = 1
            objs.s_yi.val = 33
            rft.testbench.clock()
            objs.s_xi.val = 0
            objs.s_yi.val = 42
            self.assertEqual(int(objs.s_xo), 0)
            self.assertEqual(int(objs.s_yo), 0)
            rft.testbench.clock()
            self.assertEqual(int(objs.s_xo), 1)
            self.assertEqual(int(objs.s_yo), 33)
            rft.testbench.clock()
            self.assertEqual(int(objs.s_xo), 0)
            self.assertEqual(int(objs.s_yo), 42)

    def test_internals_3(self):
        """test strobed internals connected to ports"""
        rft = RegisterFileTestbench({
            'metadata': {'name': 'test'},
            'internal-io': [
                {
                    'direction': 'strobe',
                    'internal': 'x',
                    'port': 'xa',
                },
                {
                    'direction': 'strobe',
                    'internal': 'x',
                    'port': 'xb',
                },
                {
                    'direction': 'output',
                    'internal': 'x',
                    'port': 'xo',
                },
                {
                    'direction': 'strobe',
                    'internal': 'y:8',
                    'port': 'ya',
                },
                {
                    'direction': 'strobe',
                    'internal': 'y:8',
                    'port': 'yb',
                },
                {
                    'direction': 'output',
                    'internal': 'y:8',
                    'port': 'yo',
                },
            ]})
        self.assertEqual(rft.ports, (
            'bus',
            's_xa',
            's_xb',
            's_xo',
            's_ya',
            's_yb',
            's_yo',
        ))
        with rft as objs:
            # Note: latency is two cycles; one for the entity itself, and one
            # for the testbench.
            objs.s_xa.val = 0
            objs.s_xb.val = 0
            objs.s_ya.val = 0
            objs.s_yb.val = 0
            rft.testbench.clock()
            objs.s_xa.val = 1
            objs.s_xb.val = 0
            objs.s_ya.val = 33
            objs.s_yb.val = 42
            rft.testbench.clock()
            objs.s_xa.val = 0
            objs.s_xb.val = 1
            objs.s_ya.val = 55
            objs.s_yb.val = 66
            self.assertEqual(int(objs.s_xo), 0)
            self.assertEqual(int(objs.s_yo), 0)
            rft.testbench.clock()
            self.assertEqual(int(objs.s_xo), 1)
            self.assertEqual(int(objs.s_yo), 33|42)
            rft.testbench.clock()
            self.assertEqual(int(objs.s_xo), 1)
            self.assertEqual(int(objs.s_yo), 55|66)

    def test_internals_err(self):
        """test config errors for internals"""
        with self.assertRaisesRegex(Exception, 'multiple internal I/O ports with name'):
            RegisterFileTestbench({
                'metadata': {'name': 'test'},
                'internal-io': [
                    {
                        'direction': 'input',
                        'internal': 'x',
                    },
                    {
                        'direction': 'output',
                        'internal': 'x',
                    },
                ]})

        with self.assertRaisesRegex(Exception, 'an output port expects internal signal x to '
                                    'be a vector of size 3, but it is a scalar'):
            RegisterFileTestbench({
                'metadata': {'name': 'test'},
                'internal-io': [
                    {
                        'direction': 'input',
                        'internal': 'x',
                        'port': 'xi',
                    },
                    {
                        'direction': 'output',
                        'internal': 'x:3',
                        'port': 'xo',
                    },
                ]})

        with self.assertRaisesRegex(Exception, 'an output port expects internal signal x to '
                                    'be a vector of size 3, but it is a vector of size 1'):
            RegisterFileTestbench({
                'metadata': {'name': 'test'},
                'internal-io': [
                    {
                        'direction': 'input',
                        'internal': 'x:1',
                        'port': 'xi',
                    },
                    {
                        'direction': 'output',
                        'internal': 'x:3',
                        'port': 'xo',
                    },
                ]})

        with self.assertRaisesRegex(Exception, 'multiple drivers for internal x: an input port '
                                    'and an input port'):
            RegisterFileTestbench({
                'metadata': {'name': 'test'},
                'internal-io': [
                    {
                        'direction': 'input',
                        'internal': 'x',
                        'port': 'xi',
                    },
                    {
                        'direction': 'input',
                        'internal': 'x',
                        'port': 'xo',
                    },
                ]})

        with self.assertRaisesRegex(Exception, 'internal x is never used'):
            RegisterFileTestbench({
                'metadata': {'name': 'test'},
                'internal-io': [
                    {
                        'direction': 'input',
                        'internal': 'x',
                        'port': 'xi',
                    },
                ]})

        with self.assertRaisesRegex(Exception, 'internal x is not driven by anything'):
            RegisterFileTestbench({
                'metadata': {'name': 'test'},
                'internal-io': [
                    {
                        'direction': 'output',
                        'internal': 'x',
                        'port': 'xo',
                    },
                ]})

        with self.assertRaisesRegex(Exception, 'internal x cannot both be driven by an '
                                    'input port and strobed by a strobe input port'):
            RegisterFileTestbench({
                'metadata': {'name': 'test'},
                'internal-io': [
                    {
                        'direction': 'strobe',
                        'internal': 'x',
                        'port': 'xs',
                    },
                    {
                        'direction': 'input',
                        'internal': 'x',
                        'port': 'xi',
                    },
                    {
                        'direction': 'output',
                        'internal': 'x',
                        'port': 'xo',
                    },
                ]})
