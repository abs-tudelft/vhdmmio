"""Test prot-based security."""

from unittest import TestCase
from ..testbench import RegisterFileTestbench

class TestSecurity(TestCase):
    """Test prot-based security."""

    def test_basic(self):
        """test denying access based on prot"""
        rft = RegisterFileTestbench({
            'metadata': {'name': 'test'},
            'fields': [
                {
                    'address': 0,
                    'bitrange': '15..0',
                    'name': 'a',
                    'behavior': 'control',
                    'write-allow-user': False,
                    'write-allow-nonsecure': False,
                    'write-allow-instruction': False,
                    'read-allow-secure': False,
                    'read-allow-data': False,
                },
                {
                    'address': 0,
                    'bitrange': '31..16',
                    'name': 'b',
                    'behavior': 'control',
                    'write-allow-privileged': False,
                    'write-allow-nonsecure': False,
                    'write-allow-instruction': False,
                    'read-allow-user': False,
                },
            ]})
        self.assertEqual(rft.ports, (
            'bus',
            'f_a_o.data',
            'f_b_o.data',
        ))
        with rft as objs:
            objs.bus.write(0, 0xA000A000, prot='000') # b
            objs.bus.write(0, 0xA001A001, prot='001') # a
            with self.assertRaisesRegex(ValueError, 'decode'):
                objs.bus.write(0, 0xA010A010, prot='010')
            with self.assertRaisesRegex(ValueError, 'decode'):
                objs.bus.write(0, 0xA011A011, prot='011')
            with self.assertRaisesRegex(ValueError, 'decode'):
                objs.bus.write(0, 0xA100A100, prot='100')
            with self.assertRaisesRegex(ValueError, 'decode'):
                objs.bus.write(0, 0xA101A101, prot='101')
            with self.assertRaisesRegex(ValueError, 'decode'):
                objs.bus.write(0, 0xA110A110, prot='110')
            with self.assertRaisesRegex(ValueError, 'decode'):
                objs.bus.write(0, 0xA111A111, prot='111')

            with self.assertRaisesRegex(ValueError, 'decode'):
                objs.bus.read(0, prot='000')
            self.assertEqual(objs.bus.read(0, prot='001'), 0xA0000000)
            with self.assertRaisesRegex(ValueError, 'decode'):
                objs.bus.read(0, prot='010')
            self.assertEqual(objs.bus.read(0, prot='011'), 0xA0000000)
            with self.assertRaisesRegex(ValueError, 'decode'):
                objs.bus.read(0, prot='100')
            self.assertEqual(objs.bus.read(0, prot='101'), 0xA0000000)
            self.assertEqual(objs.bus.read(0, prot='110'), 0x0000A001)
            self.assertEqual(objs.bus.read(0, prot='111'), 0xA000A001)

    def test_hardening(self):
        """test hardening"""
        rft = RegisterFileTestbench({
            'metadata': {'name': 'test'},
            #'features': {'insecure': True},
            'fields': [
                {
                    'address': 0,
                    'bitrange': '63..0',
                    'name': 'secret',
                    'behavior': 'control',
                    'write-allow-user': False,
                    'read-allow-user': False,
                },
                {
                    'address': 8,
                    'bitrange': '63..0',
                    'name': 'x',
                    'behavior': 'control',
                },
            ]})
        self.assertEqual(rft.ports, (
            'bus',
            'f_secret_o.data',
            'f_x_o.data',
        ))
        with rft as objs:
            # Privileged write.
            objs.bus.write(0, 0x11223344, prot='001')
            objs.bus.write(4, 0x55667788, prot='001')

            # Make sure that the write holding register is properly cleared.
            objs.bus.write(12, 0, strb='0000')
            self.assertEqual(objs.bus.read(8), 0)
            self.assertEqual(objs.bus.read(12), 0)

            # Privileged read.
            self.assertEqual(objs.bus.read(0, prot='001'), 0x11223344)
            self.assertEqual(objs.bus.read(4, prot='001'), 0x55667788)

            # Make sure that the read holding register is properly cleared.
            try:
                self.assertEqual(objs.bus.read(12), 0)
            except ValueError:
                pass

            # Try to change the secret by interrupting a privileged write.
            objs.bus.write(0, 0x22334455, prot='001')
            with self.assertRaisesRegex(ValueError, 'slave'):
                objs.bus.write(0, 0xDEADC0DE)
            objs.bus.write(4, 0x66778899, prot='001')
            self.assertEqual(objs.bus.read(0, prot='001'), 0x22334455)
            self.assertEqual(objs.bus.read(4, prot='001'), 0x66778899)

            # Try to read the secret by interrupting a privileged read.
            self.assertEqual(objs.bus.read(0, prot='001'), 0x22334455)
            with self.assertRaisesRegex(ValueError, 'slave'):
                objs.bus.read(4)
            self.assertEqual(objs.bus.read(4, prot='001'), 0x66778899)

    def test_error(self):
        """test prot-related error messages"""
        with self.assertRaisesRegex(Exception, 'cannot deny both user and privileged accesses'):
            RegisterFileTestbench({
                'metadata': {'name': 'test'},
                'fields': [
                    {
                        'address': 0,
                        'bitrange': '15..0',
                        'name': 'a',
                        'behavior': 'control',
                        'write-allow-user': False,
                        'write-allow-privileged': False,
                    },
                ]})

        with self.assertRaisesRegex(Exception, 'cannot deny both secure and nonsecure accesses'):
            RegisterFileTestbench({
                'metadata': {'name': 'test'},
                'fields': [
                    {
                        'address': 0,
                        'bitrange': '15..0',
                        'name': 'a',
                        'behavior': 'control',
                        'write-allow-secure': False,
                        'write-allow-nonsecure': False,
                    },
                ]})

        with self.assertRaisesRegex(Exception, 'cannot deny both data and instruction accesses'):
            RegisterFileTestbench({
                'metadata': {'name': 'test'},
                'fields': [
                    {
                        'address': 0,
                        'bitrange': '15..0',
                        'name': 'a',
                        'behavior': 'control',
                        'read-allow-data': False,
                        'read-allow-instruction': False,
                    },
                ]})
