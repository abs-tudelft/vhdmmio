"""Tests for field repetition."""

from unittest import TestCase
from ..testbench import RegisterFileTestbench

class TestFieldRepetition(TestCase):
    """Tests for field repetition."""

    def test_normal(self):
        """test normal repetition"""
        rft = RegisterFileTestbench({
            'metadata': {'name': 'test'},
            'fields': [
                {
                    'address': 0,
                    'bitrange': '7..0',
                    'repeat': 4,
                    'name': 'a',
                    'behavior': 'status',
                },
            ]})
        self.assertEqual(rft.ports, (
            'bus',
            'f_a_i.0.write_data',
            'f_a_i.1.write_data',
            'f_a_i.2.write_data',
            'f_a_i.3.write_data',
        ))
        with rft as objs:
            objs.f_a_i[0].write_data.val = 4
            objs.f_a_i[1].write_data.val = 8
            objs.f_a_i[2].write_data.val = 15
            objs.f_a_i[3].write_data.val = 16
            self.assertEqual(objs.bus.read(0), 0x100F0804)
            with self.assertRaisesRegex(ValueError, 'decode'):
                objs.bus.read(4)

    def test_reverse_stride(self):
        """test reversed field stride"""
        rft = RegisterFileTestbench({
            'metadata': {'name': 'test'},
            'fields': [
                {
                    'address': 0,
                    'bitrange': '31..24',
                    'repeat': 4,
                    'field-stride': -8,
                    'name': 'a',
                    'behavior': 'status',
                },
            ]})
        self.assertEqual(rft.ports, (
            'bus',
            'f_a_i.0.write_data',
            'f_a_i.1.write_data',
            'f_a_i.2.write_data',
            'f_a_i.3.write_data',
        ))
        with rft as objs:
            objs.f_a_i[0].write_data.val = 4
            objs.f_a_i[1].write_data.val = 8
            objs.f_a_i[2].write_data.val = 15
            objs.f_a_i[3].write_data.val = 16
            self.assertEqual(objs.bus.read(0), 0x04080F10)
            with self.assertRaisesRegex(ValueError, 'decode'):
                objs.bus.read(4)

    def test_custom_field_repeat(self):
        """test custom field repeat"""
        rft = RegisterFileTestbench({
            'metadata': {'name': 'test'},
            'fields': [
                {
                    'address': 0,
                    'bitrange': '7..0',
                    'repeat': 4,
                    'field-repeat': 2,
                    'name': 'a',
                    'behavior': 'status',
                },
            ]})
        self.assertEqual(rft.ports, (
            'bus',
            'f_a_i.0.write_data',
            'f_a_i.1.write_data',
            'f_a_i.2.write_data',
            'f_a_i.3.write_data',
        ))
        with rft as objs:
            objs.f_a_i[0].write_data.val = 4
            objs.f_a_i[1].write_data.val = 8
            objs.f_a_i[2].write_data.val = 15
            objs.f_a_i[3].write_data.val = 16
            self.assertEqual(objs.bus.read(0), 0x00000804)
            self.assertEqual(objs.bus.read(4), 0x0000100F)
            with self.assertRaisesRegex(ValueError, 'decode'):
                objs.bus.read(8)

    def test_register_repeat(self):
        """test custom field repeat and stride"""
        rft = RegisterFileTestbench({
            'metadata': {'name': 'test'},
            'fields': [
                {
                    'address': 12,
                    'bitrange': '7..0',
                    'repeat': 4,
                    'field-repeat': 1,
                    'stride': -1,
                    'name': 'a',
                    'behavior': 'status',
                },
            ]})
        self.assertEqual(rft.ports, (
            'bus',
            'f_a_i.0.write_data',
            'f_a_i.1.write_data',
            'f_a_i.2.write_data',
            'f_a_i.3.write_data',
        ))
        with rft as objs:
            objs.f_a_i[0].write_data.val = 4
            objs.f_a_i[1].write_data.val = 8
            objs.f_a_i[2].write_data.val = 15
            objs.f_a_i[3].write_data.val = 16
            self.assertEqual(objs.bus.read(0), 16)
            self.assertEqual(objs.bus.read(4), 15)
            self.assertEqual(objs.bus.read(8), 8)
            self.assertEqual(objs.bus.read(12), 4)
            with self.assertRaisesRegex(ValueError, 'decode'):
                objs.bus.read(16)

    def test_errors(self):
        """test field repetition errors"""
        with self.assertRaisesRegex(Exception, 'underflow during address addition'):
            RegisterFileTestbench({
                'metadata': {'name': 'test'},
                'fields': [
                    {
                        'address': 0,
                        'bitrange': '7..0',
                        'repeat': 4,
                        'field-repeat': 1,
                        'stride': -1,
                        'name': 'a',
                        'behavior': 'status',
                    },
                ]})

        with self.assertRaisesRegex(Exception, 'overflow during address addition'):
            RegisterFileTestbench({
                'metadata': {'name': 'test'},
                'fields': [
                    {
                        'address': 0xFFFFFFFC,
                        'bitrange': '7..0',
                        'repeat': 4,
                        'field-repeat': 1,
                        'name': 'a',
                        'behavior': 'status',
                    },
                ]})

        with self.assertRaisesRegex(Exception, 'address summand out of range'):
            RegisterFileTestbench({
                'metadata': {'name': 'test'},
                'fields': [
                    {
                        'address': 0,
                        'bitrange': '7..0',
                        'repeat': 4,
                        'field-repeat': 1,
                        'stride': 0x100000000,
                        'name': 'a',
                        'behavior': 'status',
                    },
                ]})

        with self.assertRaisesRegex(Exception, 'overflow during address addition'):
            RegisterFileTestbench({
                'metadata': {'name': 'test'},
                'fields': [
                    {
                        'address': 0xFFFFFFFC,
                        'bitrange': '7..0',
                        'repeat': 8,
                        'name': 'a',
                        'behavior': 'status',
                    },
                ]})

        with self.assertRaisesRegex(Exception, 'bit index underflow while shifting bitrange'):
            RegisterFileTestbench({
                'metadata': {'name': 'test'},
                'fields': [
                    {
                        'address': 0,
                        'bitrange': '7..0',
                        'repeat': 8,
                        'field-stride': -1,
                        'name': 'a',
                        'behavior': 'status',
                    },
                ]})
