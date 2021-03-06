"""AXI field tests."""

from unittest import TestCase
from ..testbench import RegisterFileTestbench

class TestAxiFields(TestCase):
    """AXI field tests"""

    def test_normal(self):
        """test normal AXI field"""
        rft = RegisterFileTestbench({
            'metadata': {'name': 'test'},
            'fields': [
                {
                    'address': '0x--',
                    'name': 'a',
                    'behavior': 'axi',
                    'flatten': True
                },
            ]})
        self.assertEqual(rft.ports, ('bus', 'f_a'))
        with rft as objs:

            # Test blocking.
            read_resp = []
            def read_cb(_, resp):
                read_resp.append(int(resp))
            objs.bus.async_read(read_cb, 0)

            write_resp = []
            def write_cb(resp):
                write_resp.append(int(resp))
            objs.bus.async_write(write_cb, 0, 0)

            rft.testbench.clock(20)
            self.assertEqual(read_resp, [])
            self.assertEqual(write_resp, [])

            objs.f_a.start()

            rft.testbench.clock(10)
            self.assertEqual(read_resp, [0])
            self.assertEqual(write_resp, [0])

            # Test data passthrough.
            for i in range(16):
                objs.bus.write(i * 4, hash(str(i)) & 0xFFFFFFFF)
            for i in range(16):
                self.assertEqual(objs.f_a.read(i * 4), hash(str(i)) & 0xFFFFFFFF)
                self.assertEqual(objs.bus.read(i * 4), hash(str(i)) & 0xFFFFFFFF)

            # Test error passthrough.
            objs.f_a.handle_read = lambda *_: 'error'
            objs.f_a.handle_write = lambda *_: 'error'
            with self.assertRaisesRegex(ValueError, 'slave'):
                objs.bus.read(0)
            with self.assertRaisesRegex(ValueError, 'slave'):
                objs.bus.write(0, 0)

            objs.f_a.handle_read = lambda *_: 'decode'
            objs.f_a.handle_write = lambda *_: 'decode'
            with self.assertRaisesRegex(ValueError, 'decode'):
                objs.bus.read(0)
            with self.assertRaisesRegex(ValueError, 'decode'):
                objs.bus.write(0, 0)

    def test_flattened(self):
        """test flattened AXI field"""
        rft = RegisterFileTestbench({
            'metadata': {'name': 'test'},
            'fields': [
                {
                    'address': '0x--',
                    'name': 'a',
                    'behavior': 'axi',
                    'bus-flatten': True,
                    'flatten': True
                },
            ]})
        self.assertEqual(rft.ports, (
            'bus',
            'f_a_araddr',
            'f_a_arprot',
            'f_a_arready',
            'f_a_arvalid',
            'f_a_awaddr',
            'f_a_awprot',
            'f_a_awready',
            'f_a_awvalid',
            'f_a_bready',
            'f_a_bresp',
            'f_a_bvalid',
            'f_a_rdata',
            'f_a_rready',
            'f_a_rresp',
            'f_a_rvalid',
            'f_a_uirq',
            'f_a_wdata',
            'f_a_wready',
            'f_a_wstrb',
            'f_a_wvalid',
        ))
        with rft:
            # This should probably be tested beyond just compiling. On the
            # other hand, What Could Possibly Go Wrong? (TM)
            pass

    def test_errors(self):
        """test AXI field config errors"""
        msg = ('AXI fields must be 32 or 64 bits wide')
        with self.assertRaisesRegex(Exception, msg):
            RegisterFileTestbench({
                'metadata': {'name': 'test'},
                'fields': [
                    {
                        'address': 0,
                        'bitrange': '15..0',
                        'name': 'a',
                        'behavior': 'axi',
                    },
                ]})

        msg = ('subaddress is too wide for 30-bit word address')
        with self.assertRaisesRegex(Exception, msg):
            RegisterFileTestbench({
                'metadata': {'name': 'test'},
                'fields': [
                    {
                        'address': 0,
                        'subaddress': [{'blank': 40}],
                        'name': 'a',
                        'behavior': 'axi',
                    },
                ]})
