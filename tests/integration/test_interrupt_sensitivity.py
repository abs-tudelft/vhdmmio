"""Interrupt sensitivity tests."""

from os.path import join as pjoin
import tempfile
from unittest import TestCase
from vhdmmio.html import HtmlDocumentationGenerator
from ..testbench import RegisterFileTestbench

class TestInterruptSense(TestCase):
    """Interrupt sensitivity tests"""

    def test_strobe_high(self):
        """test basic strobe-high interrupt"""
        rft = RegisterFileTestbench({
            'metadata': {'name': 'test'},
            'interrupts': [
                {
                    'name': 'x',
                },
            ],
            'fields': [
                {
                    'address': '0',
                    'bitrange': 0,
                    'name': 'x',
                    'behavior': 'interrupt-flag',
                    'interrupt': 'x',
                },
            ]})
        self.assertEqual(rft.ports, (
            'bus',
            'i_x_request',
        ))
        with tempfile.TemporaryDirectory() as tdir:
            HtmlDocumentationGenerator([rft.regfile]).generate(tdir)
            with open(pjoin(tdir, 'index.html'), 'r') as fil:
                self.assertTrue('strobe-high' in fil.read().lower())
        with rft as objs:
            self.assertEqual(objs.bus.read(0), 0)
            self.assertEqual(int(objs.bus.interrupt), 0)

            objs.i_x_request.val = 1
            rft.testbench.clock()
            objs.i_x_request.val = 0
            rft.testbench.clock()
            self.assertEqual(objs.bus.read(0), 1)
            self.assertEqual(int(objs.bus.interrupt), 1)

            objs.bus.write(0, 1)
            self.assertEqual(objs.bus.read(0), 0)
            self.assertEqual(int(objs.bus.interrupt), 0)

    def test_strobe_low(self):
        """test basic strobe-low interrupt"""
        rft = RegisterFileTestbench({
            'metadata': {'name': 'test'},
            'interrupts': [
                {
                    'name': 'x',
                    'active': 'low',
                },
            ],
            'fields': [
                {
                    'address': '0',
                    'bitrange': 0,
                    'name': 'x',
                    'behavior': 'interrupt-flag',
                    'interrupt': 'x',
                },
            ]})
        self.assertEqual(rft.ports, (
            'bus',
            'i_x_request',
        ))
        with tempfile.TemporaryDirectory() as tdir:
            HtmlDocumentationGenerator([rft.regfile]).generate(tdir)
            with open(pjoin(tdir, 'index.html'), 'r') as fil:
                self.assertTrue('strobe-low' in fil.read().lower())
        with rft as objs:
            self.assertEqual(objs.bus.read(0), 1)
            self.assertEqual(int(objs.bus.interrupt), 1)

            objs.i_x_request.val = 1
            objs.bus.write(0, 1)
            self.assertEqual(objs.bus.read(0), 0)
            self.assertEqual(int(objs.bus.interrupt), 0)

            objs.i_x_request.val = 0
            rft.testbench.clock()
            objs.i_x_request.val = 1
            rft.testbench.clock()
            self.assertEqual(objs.bus.read(0), 1)
            self.assertEqual(int(objs.bus.interrupt), 1)

            objs.bus.write(0, 1)
            self.assertEqual(objs.bus.read(0), 0)
            self.assertEqual(int(objs.bus.interrupt), 0)

    def test_level_high(self):
        """test basic level-high interrupt"""
        rft = RegisterFileTestbench({
            'metadata': {'name': 'test'},
            'interrupts': [
                {
                    'name': 'x',
                },
            ],
            'fields': [
                {
                    'address': '0',
                    'bitrange': 0,
                    'name': 'x',
                    'behavior': 'interrupt-flag',
                    'bus-write': 'disabled',
                    'interrupt': 'x',
                },
            ]})
        self.assertEqual(rft.ports, (
            'bus',
            'i_x_request',
        ))
        with tempfile.TemporaryDirectory() as tdir:
            HtmlDocumentationGenerator([rft.regfile]).generate(tdir)
            with open(pjoin(tdir, 'index.html'), 'r') as fil:
                self.assertTrue('level-high' in fil.read().lower())
        with rft as objs:
            self.assertEqual(objs.bus.read(0), 0)
            self.assertEqual(int(objs.bus.interrupt), 0)

            objs.i_x_request.val = 1
            self.assertEqual(objs.bus.read(0), 1)
            self.assertEqual(int(objs.bus.interrupt), 1)

            objs.i_x_request.val = 0
            self.assertEqual(objs.bus.read(0), 0)
            self.assertEqual(int(objs.bus.interrupt), 0)

    def test_level_low(self):
        """test basic level-low interrupt"""
        rft = RegisterFileTestbench({
            'metadata': {'name': 'test'},
            'interrupts': [
                {
                    'name': 'x',
                    'active': 'low',
                },
            ],
            'fields': [
                {
                    'address': '0',
                    'bitrange': 0,
                    'name': 'x',
                    'behavior': 'interrupt-flag',
                    'bus-write': 'disabled',
                    'interrupt': 'x',
                },
            ]})
        self.assertEqual(rft.ports, (
            'bus',
            'i_x_request',
        ))
        with tempfile.TemporaryDirectory() as tdir:
            HtmlDocumentationGenerator([rft.regfile]).generate(tdir)
            with open(pjoin(tdir, 'index.html'), 'r') as fil:
                self.assertTrue('level-low' in fil.read().lower())
        with rft as objs:
            self.assertEqual(objs.bus.read(0), 1)
            self.assertEqual(int(objs.bus.interrupt), 1)

            objs.i_x_request.val = 1
            self.assertEqual(objs.bus.read(0), 0)
            self.assertEqual(int(objs.bus.interrupt), 0)

            objs.i_x_request.val = 0
            self.assertEqual(objs.bus.read(0), 1)
            self.assertEqual(int(objs.bus.interrupt), 1)

    def test_rising(self):
        """test basic rising-edge interrupt"""
        rft = RegisterFileTestbench({
            'metadata': {'name': 'test'},
            'interrupts': [
                {
                    'name': 'x',
                    'active': 'rising',
                },
            ],
            'fields': [
                {
                    'address': '0',
                    'bitrange': 0,
                    'name': 'x',
                    'behavior': 'interrupt-flag',
                    'interrupt': 'x',
                },
            ]})
        self.assertEqual(rft.ports, (
            'bus',
            'i_x_request',
        ))
        with tempfile.TemporaryDirectory() as tdir:
            HtmlDocumentationGenerator([rft.regfile]).generate(tdir)
            with open(pjoin(tdir, 'index.html'), 'r') as fil:
                self.assertTrue('rising' in fil.read().lower())
        with rft as objs:
            self.assertEqual(objs.bus.read(0), 0)
            self.assertEqual(int(objs.bus.interrupt), 0)

            objs.i_x_request.val = 1
            rft.testbench.clock()

            self.assertEqual(objs.bus.read(0), 1)
            self.assertEqual(int(objs.bus.interrupt), 1)

            objs.bus.write(0, 1)
            self.assertEqual(objs.bus.read(0), 0)
            self.assertEqual(int(objs.bus.interrupt), 0)

            objs.i_x_request.val = 0
            rft.testbench.clock()

            self.assertEqual(objs.bus.read(0), 0)
            self.assertEqual(int(objs.bus.interrupt), 0)

    def test_falling(self):
        """test basic falling-edge interrupt"""
        rft = RegisterFileTestbench({
            'metadata': {'name': 'test'},
            'interrupts': [
                {
                    'name': 'x',
                    'active': 'falling',
                },
            ],
            'fields': [
                {
                    'address': '0',
                    'bitrange': 0,
                    'name': 'x',
                    'behavior': 'interrupt-flag',
                    'interrupt': 'x',
                },
            ]})
        self.assertEqual(rft.ports, (
            'bus',
            'i_x_request',
        ))
        with tempfile.TemporaryDirectory() as tdir:
            HtmlDocumentationGenerator([rft.regfile]).generate(tdir)
            with open(pjoin(tdir, 'index.html'), 'r') as fil:
                self.assertTrue('falling' in fil.read().lower())
        with rft as objs:
            self.assertEqual(objs.bus.read(0), 0)
            self.assertEqual(int(objs.bus.interrupt), 0)

            objs.i_x_request.val = 1
            rft.testbench.clock()

            self.assertEqual(objs.bus.read(0), 0)
            self.assertEqual(int(objs.bus.interrupt), 0)

            objs.i_x_request.val = 0
            rft.testbench.clock()

            self.assertEqual(objs.bus.read(0), 1)
            self.assertEqual(int(objs.bus.interrupt), 1)

            objs.bus.write(0, 1)
            self.assertEqual(objs.bus.read(0), 0)
            self.assertEqual(int(objs.bus.interrupt), 0)

    def test_edge(self):
        """test basic edge-sensitive interrupt"""
        rft = RegisterFileTestbench({
            'metadata': {'name': 'test'},
            'interrupts': [
                {
                    'name': 'x',
                    'active': 'edge',
                },
            ],
            'fields': [
                {
                    'address': '0',
                    'bitrange': 0,
                    'name': 'x',
                    'behavior': 'interrupt-flag',
                    'interrupt': 'x',
                },
            ]})
        self.assertEqual(rft.ports, (
            'bus',
            'i_x_request',
        ))
        with tempfile.TemporaryDirectory() as tdir:
            HtmlDocumentationGenerator([rft.regfile]).generate(tdir)
            with open(pjoin(tdir, 'index.html'), 'r') as fil:
                self.assertTrue('edge' in fil.read().lower())
        with rft as objs:
            self.assertEqual(objs.bus.read(0), 0)
            self.assertEqual(int(objs.bus.interrupt), 0)

            objs.i_x_request.val = 1
            rft.testbench.clock()

            self.assertEqual(objs.bus.read(0), 1)
            self.assertEqual(int(objs.bus.interrupt), 1)

            objs.bus.write(0, 1)
            self.assertEqual(objs.bus.read(0), 0)
            self.assertEqual(int(objs.bus.interrupt), 0)

            objs.i_x_request.val = 0
            rft.testbench.clock()

            self.assertEqual(objs.bus.read(0), 1)
            self.assertEqual(int(objs.bus.interrupt), 1)

            objs.bus.write(0, 1)
            self.assertEqual(objs.bus.read(0), 0)
            self.assertEqual(int(objs.bus.interrupt), 0)

    def test_edge_vec(self):
        """test vector edge-sensitive interrupt"""
        rft = RegisterFileTestbench({
            'metadata': {'name': 'test'},
            'interrupts': [
                {
                    'name': 'x',
                    'active': 'edge',
                    'repeat': 3,
                },
            ],
            'fields': [
                {
                    'address': '0',
                    'repeat': 3,
                    'bitrange': 0,
                    'name': 'x',
                    'behavior': 'interrupt-flag',
                    'interrupt': 'x',
                },
            ]})
        self.assertEqual(rft.ports, (
            'bus',
            'i_x_request',
        ))
        with rft as objs:
            self.assertEqual(objs.bus.read(0), 0)
            self.assertEqual(int(objs.bus.interrupt), 0)

            objs.i_x_request.val = 1
            rft.testbench.clock()

            self.assertEqual(objs.bus.read(0), 1)
            self.assertEqual(int(objs.bus.interrupt), 1)

            objs.bus.write(0, 1)
            self.assertEqual(objs.bus.read(0), 0)
            self.assertEqual(int(objs.bus.interrupt), 0)

            objs.i_x_request.val = 5
            rft.testbench.clock()

            self.assertEqual(objs.bus.read(0), 4)
            self.assertEqual(int(objs.bus.interrupt), 1)

            objs.bus.write(0, 4)
            self.assertEqual(objs.bus.read(0), 0)
            self.assertEqual(int(objs.bus.interrupt), 0)

            objs.i_x_request.val = 3
            rft.testbench.clock()

            self.assertEqual(objs.bus.read(0), 6)
            self.assertEqual(int(objs.bus.interrupt), 1)

            objs.bus.write(0, 6)
            self.assertEqual(objs.bus.read(0), 0)
            self.assertEqual(int(objs.bus.interrupt), 0)

    def test_error(self):
        """test error for event interrupts without clear"""
        for active in ['rising', 'falling', 'edge']:
            with self.assertRaisesRegex(
                    Exception, 'interrupt cannot be edge-sensitive if there '
                    'is no field that can clear the interrupt flag afterwards'):
                RegisterFileTestbench({
                    'metadata': {'name': 'test'},
                    'interrupts': [
                        {
                            'name': 'x',
                            'active': active,
                        },
                    ]})
