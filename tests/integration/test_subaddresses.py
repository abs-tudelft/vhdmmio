"""Subaddress tests using custom fields."""

from copy import deepcopy
from unittest import TestCase
from ..testbench import RegisterFileTestbench

class TestSubaddresses(TestCase):
    """Subaddress tests using custom fields."""

    @staticmethod
    def _make_config(read_addr, write_addr, sub_config, sub_offset, sub_width, page_bits=0):
        regs = {
            'metadata': {'name': 'test'},
            'fields': [
                {
                    'address': read_addr,
                    'bitrange': '%d..0' % (sub_width - 1),
                    'subaddress': deepcopy(sub_config),
                    'subaddress-offset': sub_offset,
                    'name': 'a',
                    'behavior': 'custom',
                    'read': (
                        '$data$ := $sub$;\n'
                        '$ack$ := true;\n'
                    ),
                },
                {
                    'address': write_addr,
                    'bitrange': '%d..0' % (sub_width - 1),
                    'subaddress': deepcopy(sub_config),
                    'subaddress-offset': sub_offset,
                    'name': 'b',
                    'behavior': 'custom',
                    'interfaces': [{'state': 'data:%d' % sub_width}],
                    'read': (
                        '$data$ := $s.data$;\n'
                        '$ack$ := true;\n'
                    ),
                    'write': (
                        '$s.data$ := $sub$;\n'
                        '$ack$ := true;\n'
                    ),
                },
            ]
        }
        if page_bits:
            regs['fields'].append({
                'address': 0x2000,
                'bitrange': '%d..0' % (page_bits - 1),
                'name': 'page',
                'behavior': 'internal-control',
                'internal': 'page'})
        return regs

    def test_default_normal(self):
        """test default subaddress for normal field"""
        rft = RegisterFileTestbench(self._make_config(
            read_addr=0x0000,
            write_addr=0x1000,
            sub_config=[],
            sub_offset=0,
            sub_width=1))
        with rft as objs:
            self.assertEqual(objs.bus.read(0x0000), 0)
            objs.bus.write(0x1000, 0)
            self.assertEqual(objs.bus.read(0x1000), 0)

    def test_default_offset(self):
        """test default subaddress on LSB side of address with offset"""
        rft = RegisterFileTestbench(self._make_config(
            read_addr='0x0000/5',
            write_addr='0x1000/5',
            sub_config=[],
            sub_offset=3,
            sub_width=3))
        with rft as objs:
            for i in range(8):
                self.assertEqual(objs.bus.read(i * 4), (i + 3) % 8)
            for i in range(8):
                objs.bus.write(0x1000 + i * 4, 0)
                self.assertEqual(objs.bus.read(0x1000), (i + 3) % 8)

    def test_default_middle(self):
        """test default subaddress in the middle of an address"""
        rft = RegisterFileTestbench(self._make_config(
            read_addr='0b000000---00--',
            write_addr='0b100000---00--',
            sub_config=[],
            sub_offset=0,
            sub_width=3))
        with rft as objs:
            for i in range(8):
                self.assertEqual(objs.bus.read(i * 16), i)
            for i in range(8):
                objs.bus.write(0x1000 + i * 16, 0)
                self.assertEqual(objs.bus.read(0x1000), i)

    def test_custom(self):
        """test custom subaddress"""
        rft = RegisterFileTestbench(self._make_config(
            read_addr='0b000000-------',
            write_addr='0b100000-------',
            sub_config=[
                {'blank': 2},
                {'address': '6..4'},
                {'address': 2},
                {'internal': 'page:4'},
                {'internal': 'page:4', 'internal-bitrange': 2},
            ],
            sub_offset=0,
            sub_width=11,
            page_bits=4))
        with rft as objs:
            objs.bus.write(0x2000, 0b0000)
            self.assertEqual(objs.bus.read(0b0000000), 0b00000000000)
            self.assertEqual(objs.bus.read(0b0000100), 0b00000100000)
            self.assertEqual(objs.bus.read(0b0001000), 0b00000000000)
            self.assertEqual(objs.bus.read(0b0010000), 0b00000000100)
            self.assertEqual(objs.bus.read(0b0100000), 0b00000001000)
            self.assertEqual(objs.bus.read(0b1000000), 0b00000010000)
            objs.bus.write(0x2000, 0b0001)
            self.assertEqual(objs.bus.read(0b0000000), 0b00001000000)
            objs.bus.write(0x2000, 0b0010)
            self.assertEqual(objs.bus.read(0b0000000), 0b00010000000)
            objs.bus.write(0x2000, 0b0100)
            self.assertEqual(objs.bus.read(0b0000000), 0b10100000000)
            objs.bus.write(0x2000, 0b1000)
            self.assertEqual(objs.bus.read(0b0000000), 0b01000000000)
