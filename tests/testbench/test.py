"""Self-tests for the testbench generator submodule."""

import os
from unittest import TestCase
from .main import Testbench
from .streams import StreamSourceMock, StreamSinkMock
from .axi import AXI4LMasterMock, AXI4LSlaveMock
from .regfile import RegisterFileTestbench

class TestTestbench(TestCase):
    """Self-tests for the testbench generator submodule."""

    def test_basic(self):
        """testbench self-test: basic functionality"""
        testbench = Testbench()
        testbench.add_include(os.path.dirname(__file__) + '/../../vhdmmio/vhdl/vhdmmio_pkg.vhd')
        test_in = testbench.add_input('test_in', 8)
        test_out = testbench.add_output('test_out', 8)
        testbench.add_body('test_out <= std_logic_vector(unsigned(test_in) + 1);')
        with testbench:
            self.assertEqual(test_in.val, '00000000')
            self.assertEqual(int(test_in), 0)
            test_in.val = 33
            self.assertEqual(test_in.val, '00100001')
            self.assertEqual(int(test_in), 33)

            self.assertEqual(test_out.val, '00000000')
            self.assertEqual(int(test_out), 0)
            testbench.clock()
            self.assertEqual(test_out.val, '00100010')
            self.assertEqual(int(test_out), 34)

    def test_streams(self):
        """testbench self-test: streams"""
        testbench = Testbench()
        testbench.add_include(os.path.dirname(__file__) + '/../../vhdmmio/vhdl/vhdmmio_pkg.vhd')
        test_source = StreamSourceMock(
            testbench.add_input('source_valid'),
            testbench.add_output('source_ready'),
            testbench.add_input('source_data', 8))
        test_sink = StreamSinkMock(
            testbench.add_output('sink_valid'),
            testbench.add_input('sink_ready'),
            testbench.add_output('sink_data', 8))
        testbench.add_body('sink_data <= std_logic_vector(unsigned(source_data) + 1);')
        testbench.add_body('sink_valid <= source_valid;')
        testbench.add_body('source_ready <= sink_ready;')
        with testbench:
            test_source.send(33)
            with self.assertRaises(TimeoutError):
                test_source.wait(10)
            value = []
            def handler(data):
                value.append(int(data))
            test_sink.handle(handler)
            test_source.wait(10)
            self.assertEqual(value, [34])

    def test_axi(self):
        """testbench self-test: AXI4-lite"""
        testbench = Testbench()
        testbench.add_include(os.path.dirname(__file__) + '/../../vhdmmio/vhdl/vhdmmio_pkg.vhd')
        master = AXI4LMasterMock(testbench, 'master')
        slave = AXI4LSlaveMock(testbench, 'slave')
        testbench.add_body('slave_req <= master_req;')
        testbench.add_body('master_resp <= slave_resp;')
        with testbench:
            slave.start()
            self.assertEqual(master.read_bits(0), 'X'*32)
            master.write(0, 33)
            self.assertEqual(master.read(0), 33)

    def test_register_file(self):
        """testbench self-test: empty register file"""
        testbench = RegisterFileTestbench({'metadata': {'name': 'test'}})
        with testbench as objs:
            with self.assertRaisesRegex(ValueError, 'decode error'):
                objs.bus.read(0)
            with self.assertRaisesRegex(ValueError, 'decode error'):
                objs.bus.write(0, 0)
