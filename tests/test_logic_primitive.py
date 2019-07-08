"""Tests for primitive fields and derivatives."""

from unittest import TestCase
from .testbench import RegisterFileTestbench, StreamSourceMock, StreamSinkMock

class TestPrimitive(TestCase):
    """Tests for primitive fields and derivatives."""

    def test_constant(self):
        """test constant fields"""
        rft = RegisterFileTestbench({
            'meta': {'name': 'test'},
            'features': {'bus-width': 32, 'optimize': True},
            'fields': [
                {
                    'address': '0x00:3..0',
                    'register-name': 'a',
                    'name': 'a',
                    'type': 'constant',
                    'value': 10,
                },
                {
                    'address': '0x00:4',
                    'name': 'b',
                    'type': 'constant',
                    'repeat': 3,
                    'value': 1,
                },
                {
                    'address': '0x04',
                    'name': 'c',
                    'type': 'constant',
                    'value': 0xCAFEBABE
                },
            ]
        })
        with rft as objs:

            # Test bus reads.
            self.assertEqual(objs.bus.read(0), 0x7A)
            self.assertEqual(objs.bus.read(4), 0xCAFEBABE)

            # Test bus writes.
            with self.assertRaisesRegex(ValueError, 'decode error'):
                objs.bus.write(0, 33)

    def test_config(self):
        """test config fields"""
        rft = RegisterFileTestbench(
            {
                'meta': {'name': 'test'},
                'features': {'bus-width': 32, 'optimize': True},
                'fields': [
                    {
                        'address': '0x00:3..0',
                        'register-name': 'a',
                        'name': 'a',
                        'type': 'config',
                    },
                    {
                        'address': '0x00:4',
                        'name': 'b',
                        'type': 'config',
                        'repeat': 3,
                    },
                    {
                        'address': '0x04',
                        'name': 'c',
                        'type': 'config',
                    },
                ]
            },
            ('F_A_RESET_DATA', '"1010"'),
            ('F_B_RESET_DATA', "(0 => '1', 1 => '0', 2 => '0')"),
            ('F_C_RESET_DATA', 'X"CAFEBABE"'))
        with rft as objs:

            # Test bus reads.
            self.assertEqual(objs.bus.read(0), 0x1A)
            self.assertEqual(objs.bus.read(4), 0xCAFEBABE)

            # Test bus writes.
            with self.assertRaisesRegex(ValueError, 'decode error'):
                objs.bus.write(0, 33)

    def test_status(self):
        """test status fields"""
        rft = RegisterFileTestbench({
            'meta': {'name': 'test'},
            'features': {'bus-width': 32, 'optimize': True},
            'fields': [
                {
                    'address': '0x00:3..0',
                    'register-name': 'a',
                    'name': 'a',
                    'type': 'status',
                },
                {
                    'address': '0x00:4',
                    'name': 'b',
                    'type': 'status',
                    'repeat': 3,
                },
                {
                    'address': '0x04',
                    'name': 'c',
                    'type': 'status',
                },
            ]
        })
        with rft as objs:

            # Test bus reads.
            self.assertEqual(objs.bus.read(0), 0)
            self.assertEqual(objs.bus.read(4), 0)

            # Test bus writes.
            with self.assertRaisesRegex(ValueError, 'decode error'):
                objs.bus.write(0, 33)

            # Test hardware "write".
            objs.f_a_i.write_data.val = 3
            rft.testbench.clock()
            self.assertEqual(objs.bus.read(0), 0x03)
            self.assertEqual(objs.bus.read(4), 0x00000000)
            objs.f_a_i.write_data.val = 2
            objs.f_b_i[1].write_data.val = 1
            objs.f_c_i.write_data.val = 0xDEADC0DE
            rft.testbench.clock()
            self.assertEqual(objs.bus.read(0), 0x22)
            self.assertEqual(objs.bus.read(4), 0xDEADC0DE)

    def test_latching(self):
        """test latching fields"""
        rft = RegisterFileTestbench({
            'meta': {'name': 'test'},
            'features': {'bus-width': 32, 'optimize': True},
            'fields': [
                {
                    'address': '0x00:3..0',
                    'register-name': 'a',
                    'name': 'a',
                    'type': 'latching',
                },
                {
                    'address': '0x00:4',
                    'name': 'b',
                    'type': 'latching',
                    'repeat': 3,
                },
                {
                    'address': '0x04',
                    'name': 'c',
                    'type': 'latching',
                },
            ]
        })
        with rft as objs:

            # Test bus reads.
            self.assertEqual(objs.bus.read(0), 0)
            self.assertEqual(objs.bus.read(4), 0)

            # Test bus writes.
            with self.assertRaisesRegex(ValueError, 'decode error'):
                objs.bus.write(0, 33)

            # Test hardware write.
            objs.f_a_i.write_data.val = 2
            objs.f_b_i[1].write_data.val = 1
            objs.f_c_i.write_data.val = 0xDEADC0DE
            rft.testbench.clock()
            self.assertEqual(objs.bus.read(0), 0)
            self.assertEqual(objs.bus.read(4), 0)
            objs.f_b_i[1].write_enable.val = 1
            rft.testbench.clock()
            objs.f_b_i[1].write_enable.val = 0
            rft.testbench.clock()
            self.assertEqual(objs.bus.read(0), 0x20)
            self.assertEqual(objs.bus.read(4), 0)
            objs.f_a_i.write_enable.val = 1
            objs.f_c_i.write_enable.val = 1
            rft.testbench.clock()
            objs.f_a_i.write_enable.val = 0
            objs.f_c_i.write_enable.val = 0
            objs.f_a_i.write_data.val = 0
            objs.f_c_i.write_data.val = 0
            rft.testbench.clock()
            self.assertEqual(objs.bus.read(0), 0x22)
            self.assertEqual(objs.bus.read(4), 0xDEADC0DE)

    def test_stream_to_mmio(self):
        """test stream-to-mmio fields"""
        rft = RegisterFileTestbench({
            'meta': {'name': 'test'},
            'features': {'bus-width': 32, 'optimize': True},
            'fields': [
                { # block when out of data
                    'address': '0x00',
                    'name': 'a',
                    'type': 'stream-to-mmio',
                },
                { # slave error when out of data
                    'address': '0x04',
                    'name': 'b',
                    'type': 'stream-to-mmio',
                    'bus-read': 'valid-only',
                },
                { # garbage when out of data
                    'address': '0x08',
                    'name': 'c',
                    'type': 'stream-to-mmio',
                    'bus-read': 'enabled',
                },
                { # slave error when out of data, valid after reset
                    'address': '0x0C',
                    'name': 'd',
                    'type': 'stream-to-mmio',
                    'bus-read': 'valid-only',
                    'reset': 11,
                },
            ]
        })
        with rft as objs:
            mock_a = StreamSourceMock(objs.f_a_i.valid, objs.f_a_o.ready, objs.f_a_i.data)
            mock_b = StreamSourceMock(objs.f_b_i.valid, objs.f_b_o.ready, objs.f_b_i.data)
            mock_c = StreamSourceMock(objs.f_c_i.valid, objs.f_c_o.ready, objs.f_c_i.data)
            mock_d = StreamSourceMock(objs.f_d_i.valid, objs.f_d_o.ready, objs.f_d_i.data)

            async_data = []
            def callback(data, resp):
                async_data.append((resp.to_x01(), int(data)))

            # Test default configuration.
            objs.bus.async_read(callback, 0)
            rft.testbench.clock(30)
            self.assertEqual(async_data, [])
            mock_a.send(33)
            mock_a.send(55)
            mock_a.send(77)
            mock_a.send(99)
            rft.testbench.clock(10)
            self.assertEqual(async_data, [('00', 33)])
            async_data.clear()
            self.assertEqual(objs.bus.read(0), 55)
            self.assertEqual(objs.bus.read(0), 77)
            self.assertEqual(objs.bus.read(0), 99)

            # Test slave error when out of data.
            with self.assertRaisesRegex(ValueError, 'slave error'):
                objs.bus.read(4)
            mock_b.send(33)
            mock_b.send(55)
            rft.testbench.clock(10)
            async_data.clear()
            self.assertEqual(objs.bus.read(4), 33)
            self.assertEqual(objs.bus.read(4), 55)
            with self.assertRaisesRegex(ValueError, 'slave error'):
                objs.bus.read(4)

            # Test garbage when out of data.
            objs.bus.read(8)
            mock_c.send(33)
            mock_c.send(55)
            rft.testbench.clock(10)
            async_data.clear()
            self.assertEqual(objs.bus.read(8), 33)
            self.assertEqual(objs.bus.read(8), 55)
            objs.bus.read(8)

            # Test slave error when out of data, valid after reset.
            self.assertEqual(objs.bus.read(12), 11)
            with self.assertRaisesRegex(ValueError, 'slave error'):
                objs.bus.read(12)
            mock_d.send(33)
            mock_d.send(55)
            rft.testbench.clock(10)
            async_data.clear()
            self.assertEqual(objs.bus.read(12), 33)
            self.assertEqual(objs.bus.read(12), 55)
            with self.assertRaisesRegex(ValueError, 'slave error'):
                objs.bus.read(12)

            # Test bus writes.
            with self.assertRaisesRegex(ValueError, 'decode error'):
                objs.bus.write(0, 33)

    def test_mmio_to_stream(self):
        """test mmio-to-stream fields"""
        rft = RegisterFileTestbench({
            'meta': {'name': 'test'},
            'features': {'bus-width': 32, 'optimize': True},
            'fields': [
                { # block when out of data
                    'address': '0x00',
                    'name': 'a',
                    'type': 'mmio-to-stream',
                },
                { # slave error upon overflow
                    'address': '0x04',
                    'name': 'b',
                    'type': 'mmio-to-stream',
                    'bus-write': 'invalid-only',
                },
                { # slave error upon overflow, valid after reset
                    'address': '0x08',
                    'name': 'c',
                    'type': 'mmio-to-stream',
                    'bus-write': 'invalid-only',
                    'reset': 11,
                },
            ]
        })
        with rft as objs:
            mock_a = StreamSinkMock(objs.f_a_o.valid, objs.f_a_i.ready, objs.f_a_o.data)
            mock_b = StreamSinkMock(objs.f_b_o.valid, objs.f_b_i.ready, objs.f_b_o.data)
            mock_c = StreamSinkMock(objs.f_c_o.valid, objs.f_c_i.ready, objs.f_c_o.data)

            async_resp = []
            def callback(resp):
                async_resp.append(resp.to_x01())

            async_data = []
            def handler(data):
                async_data.append(int(data))

            # Test default configuration.
            objs.bus.write(0, 33)
            objs.bus.async_write(callback, 0, 55)
            rft.testbench.clock(30)
            self.assertEqual(async_resp, [])
            mock_a.handle(handler)
            rft.testbench.clock(10)
            self.assertEqual(async_data, [33])
            self.assertEqual(async_resp, ['00'])
            async_data.clear()
            async_resp.clear()
            mock_a.handle(handler)
            rft.testbench.clock(10)
            self.assertEqual(async_data, [55])
            async_data.clear()

            # Test slave error upon overflow.
            objs.bus.write(4, 33)
            with self.assertRaisesRegex(ValueError, 'slave error'):
                objs.bus.write(4, 44)
            mock_b.handle(handler)
            mock_b.wait(10)
            self.assertEqual(async_data, [33])
            async_data.clear()
            mock_b.handle(handler)
            with self.assertRaises(TimeoutError):
                mock_b.wait(10)
            objs.bus.write(4, 55)
            mock_b.wait(10)
            self.assertEqual(async_data, [55])
            async_data.clear()

            # Test slave error upon overflow, valid after reset.
            with self.assertRaisesRegex(ValueError, 'slave error'):
                objs.bus.write(8, 44)
            mock_c.handle(handler)
            mock_c.wait(10)
            self.assertEqual(async_data, [11])
            async_data.clear()
            mock_c.handle(handler)
            with self.assertRaises(TimeoutError):
                mock_c.wait(10)
            objs.bus.write(8, 55)
            mock_c.wait(10)
            self.assertEqual(async_data, [55])
            async_data.clear()

            # Test bus reads.
            with self.assertRaisesRegex(ValueError, 'decode error'):
                objs.bus.read(0)

    def test_control(self):
        """test control fields"""
        rft = RegisterFileTestbench({
            'meta': {'name': 'test'},
            'features': {'bus-width': 32, 'optimize': True},
            'fields': [
                {
                    'address': '0x00:3..0',
                    'register-name': 'a',
                    'name': 'a',
                    'type': 'control',
                },
                {
                    'address': '0x00:4',
                    'name': 'b',
                    'type': 'control',
                    'repeat': 3,
                },
                {
                    'address': '0x04',
                    'name': 'c',
                    'type': 'control',
                },
            ]
        })
        with rft as objs:

            # Test reset value and a basic 4-bit field.
            self.assertEqual(int(objs.f_a_o.data), 0)
            self.assertEqual(objs.bus.read(0), 0)
            objs.bus.write(0, 3)
            self.assertEqual(int(objs.f_a_o.data), 3)
            self.assertEqual(objs.bus.read(0), 3)

            # Test masked write access.
            self.assertEqual(int(objs.f_c_o.data), 0)
            objs.bus.write(4, 0xDEADBEEF)
            self.assertEqual(int(objs.f_a_o.data), 3)
            self.assertEqual(int(objs.f_c_o.data), 0xDEADBEEF)
            objs.bus.write(4, 0x33333333, 2)
            self.assertEqual(int(objs.f_c_o.data), 0xDEAD33EF)
            self.assertEqual(objs.bus.read(4), 0xDEAD33EF)

            # Test an array of std_logic fields.
            for i in range(3):
                self.assertEqual(int(objs.f_b_o[i].data), 0)
            objs.bus.write(0, 0x30)
            self.assertEqual(int(objs.f_b_o[0].data), 1)
            self.assertEqual(int(objs.f_b_o[1].data), 1)
            self.assertEqual(int(objs.f_b_o[2].data), 0)

    def test_flag(self):
        """test flag fields"""
        rft = RegisterFileTestbench({
            'meta': {'name': 'test'},
            'features': {'bus-width': 32, 'optimize': False},
            'fields': [
                {
                    'address': '0x00:7..0',
                    'register-name': 'a',
                    'name': 'a',
                    'type': 'flag',
                    'reset': 3,
                },
                {
                    'address': '0x04:0',
                    'repeat': 8,
                    'register-name': 'b',
                    'name': 'b',
                    'type': 'volatile-flag',
                },
                {
                    'address': '0x08:7..0',
                    'register-name': 'c',
                    'name': 'c',
                    'type': 'reverse-flag',
                },
            ]
        })
        with rft as objs:

            # Test reset values.
            self.assertEqual(int(objs.f_a_o.data), 3)
            self.assertEqual(int(objs.f_b_o[0].data), 0)
            self.assertEqual(int(objs.f_b_o[1].data), 0)
            self.assertEqual(int(objs.f_b_o[4].data), 0)
            self.assertEqual(int(objs.f_c_o.data), 0)
            self.assertEqual(objs.bus.read(0), 3)
            self.assertEqual(objs.bus.read(4), 0)
            self.assertEqual(objs.bus.read(8), 0)

            # Test asserting flags.
            objs.f_a_i.bit_set.val = 6
            objs.f_b_i[1].bit_set.val = 1
            objs.f_b_i[4].bit_set.val = 1
            rft.testbench.clock()
            objs.f_a_i.bit_set.val = 0
            objs.f_b_i[1].bit_set.val = 0
            objs.f_b_i[4].bit_set.val = 0
            rft.testbench.clock()
            objs.bus.write(8, 3)
            objs.bus.write(8, 5)
            objs.bus.write(8, 10, 2)
            self.assertEqual(int(objs.f_a_o.data), 7)
            self.assertEqual(int(objs.f_b_o[0].data), 0)
            self.assertEqual(int(objs.f_b_o[1].data), 1)
            self.assertEqual(int(objs.f_b_o[4].data), 1)
            self.assertEqual(int(objs.f_c_o.data), 7)
            self.assertEqual(objs.bus.read(0), 7)
            self.assertEqual(objs.bus.read(4), 18)
            self.assertEqual(objs.bus.read(8), 7)

            # Test clearing volatile flags.
            self.assertEqual(int(objs.f_a_o.data), 7)
            self.assertEqual(int(objs.f_b_o[0].data), 0)
            self.assertEqual(int(objs.f_b_o[1].data), 0)
            self.assertEqual(int(objs.f_b_o[4].data), 0)
            self.assertEqual(objs.bus.read(0), 7)
            self.assertEqual(objs.bus.read(4), 0)

            # Test clearing normal flags.
            objs.bus.write(0, 14)
            with self.assertRaisesRegex(ValueError, 'decode error'):
                objs.bus.write(4, 0xFF)
            self.assertEqual(int(objs.f_a_o.data), 1)
            self.assertEqual(int(objs.f_b_o[0].data), 0)
            self.assertEqual(int(objs.f_b_o[1].data), 0)
            self.assertEqual(int(objs.f_b_o[4].data), 0)
            self.assertEqual(objs.bus.read(0), 1)
            self.assertEqual(objs.bus.read(4), 0)

            # Test clearing reverse flags.
            objs.f_c_i.bit_clear.val = 6
            rft.testbench.clock()
            objs.f_c_i.bit_clear.val = 0
            rft.testbench.clock()
            self.assertEqual(int(objs.f_c_o.data), 1)
            self.assertEqual(objs.bus.read(8), 1)

    def test_counter(self):
        """test counter fields"""
        rft = RegisterFileTestbench({
            'meta': {'name': 'test'},
            'features': {'bus-width': 32, 'optimize': False},
            'fields': [
                {
                    'address': '0x00:7..0',
                    'register-name': 'a',
                    'name': 'a',
                    'type': 'counter',
                    'reset': 3,
                },
                {
                    'address': '0x04:7..0',
                    'repeat': 2,
                    'register-name': 'b',
                    'name': 'b',
                    'type': 'volatile-counter',
                },
                {
                    'address': '0x08:7..0',
                    'register-name': 'c',
                    'name': 'c',
                    'type': 'reverse-counter',
                },
            ]
        })
        with rft as objs:

            # Test reset values.
            self.assertEqual(int(objs.f_a_o.data), 3)
            self.assertEqual(int(objs.f_b_o[0].data), 0)
            self.assertEqual(int(objs.f_b_o[1].data), 0)
            self.assertEqual(int(objs.f_c_o.data), 0)
            self.assertEqual(objs.bus.read(0), 3)
            self.assertEqual(objs.bus.read(4), 0)
            self.assertEqual(objs.bus.read(8), 0)

            # Test registration of some events.
            objs.f_a_i.increment.val = 1
            objs.f_b_i[1].increment.val = 1
            rft.testbench.clock(10)
            objs.f_a_i.increment.val = 0
            objs.f_b_i[0].increment.val = 1
            rft.testbench.clock(5)
            objs.f_b_i[0].increment.val = 0
            objs.f_b_i[1].increment.val = 0
            objs.bus.write(8, 20)
            objs.bus.write(8, 22)
            rft.testbench.clock(5)
            self.assertEqual(int(objs.f_a_o.data), 13)
            self.assertEqual(int(objs.f_b_o[0].data), 5)
            self.assertEqual(int(objs.f_b_o[1].data), 15)
            self.assertEqual(int(objs.f_c_o.data), 42)
            self.assertEqual(objs.bus.read(0), 13)
            self.assertEqual(objs.bus.read(4), 0x0F05)
            self.assertEqual(objs.bus.read(8), 42)

            # Test clearing volatile counters.
            self.assertEqual(int(objs.f_a_o.data), 13)
            self.assertEqual(int(objs.f_b_o[0].data), 0)
            self.assertEqual(int(objs.f_b_o[1].data), 0)
            self.assertEqual(int(objs.f_c_o.data), 42)
            self.assertEqual(objs.bus.read(0), 13)
            self.assertEqual(objs.bus.read(4), 0)
            self.assertEqual(objs.bus.read(8), 42)

            # Test clearing normal counters.
            objs.bus.write(0, 10)
            with self.assertRaisesRegex(ValueError, 'decode error'):
                objs.bus.write(4, 0xFF)
            self.assertEqual(int(objs.f_a_o.data), 3)
            self.assertEqual(int(objs.f_b_o[0].data), 0)
            self.assertEqual(int(objs.f_b_o[1].data), 0)
            self.assertEqual(int(objs.f_c_o.data), 42)
            self.assertEqual(objs.bus.read(0), 3)
            self.assertEqual(objs.bus.read(4), 0)
            self.assertEqual(objs.bus.read(8), 42)

            # Test clearing reverse counters.
            objs.f_c_i.clear.val = 1
            rft.testbench.clock()
            objs.f_c_i.clear.val = 0 # clear is actually 1 during this cycle
            self.assertEqual(int(objs.f_c_o.data), 42)
            rft.testbench.clock()
            self.assertEqual(int(objs.f_c_o.data), 0)
            self.assertEqual(objs.bus.read(8), 0)
