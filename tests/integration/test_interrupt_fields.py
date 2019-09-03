"""Interrupt field tests."""

from copy import deepcopy
from unittest import TestCase
from ..testbench import RegisterFileTestbench

class TestInterruptFields(TestCase):
    """Interrupt field tests"""

    def test_fields(self):
        """test interrupt fields"""
        fields = []
        types = {
            typ: idx * 4 for idx, typ in enumerate([
                'volatile', 'flag', 'pend', 'enable', 'unmask', 'status', 'raw'])}
        for typ, address in types.items():
            typ_name = 'interrupt-%s' % typ
            if typ == 'volatile':
                typ_name = 'volatile-interrupt-flag'
            fields.append({
                'address': address,
                'bitrange': 0,
                'repeat': 8,
                'name': 'x_%s' % typ,
                'behavior': typ_name,
                'interrupt': 'x',
            })
            if typ not in ('volatile', 'pend'):
                fields.append({
                    'address': address,
                    'bitrange': 8,
                    'repeat': 4,
                    'name': 'y_%s' % typ,
                    'behavior': typ_name,
                    'interrupt': 'y',
                })
            if typ == 'flag':
                fields[-1]['bus-write'] = 'disabled'
        rft = RegisterFileTestbench({
            'metadata': {'name': 'test'},
            'interrupts': [
                {
                    'repeat': 8,
                    'name': 'x',
                },
                {
                    'repeat': 4,
                    'name': 'y',
                },
            ],
            'fields': fields})
        self.assertEqual(rft.ports, (
            'bus',
            'i_x_request',
            'i_y_request',
        ))
        with rft as objs:
            objs.bus.write(types['enable'], 0x555)
            objs.bus.write(types['unmask'], 0x333)
            self.assertEqual(objs.bus.read(types['enable']), 0x555)
            self.assertEqual(objs.bus.read(types['unmask']), 0x333)
            self.assertEqual(int(objs.bus.interrupt), 0)

            objs.i_x_request.val = 0xFF
            objs.i_y_request.val = 0xF

            self.assertEqual(objs.bus.read(types['raw']), 0xFFF)
            self.assertEqual(objs.bus.read(types['flag']), 0x555)
            self.assertEqual(objs.bus.read(types['status']), 0x111)
            self.assertEqual(objs.bus.read(types['volatile']), 0x055)
            self.assertEqual(objs.bus.read(types['raw']), 0xFFF)
            self.assertEqual(objs.bus.read(types['flag']), 0x555)
            self.assertEqual(objs.bus.read(types['status']), 0x111)

            objs.i_x_request.val = 0x00
            objs.i_y_request.val = 0x0

            self.assertEqual(objs.bus.read(types['raw']), 0x000)
            self.assertEqual(objs.bus.read(types['flag']), 0x055)
            self.assertEqual(objs.bus.read(types['status']), 0x011)
            objs.bus.write(types['flag'], 0x00F)
            self.assertEqual(objs.bus.read(types['flag']), 0x050)
            self.assertEqual(objs.bus.read(types['status']), 0x010)
            objs.bus.write(types['unmask'], 0xFFF)
            self.assertEqual(objs.bus.read(types['status']), 0x050)
            self.assertEqual(int(objs.bus.interrupt), 1)
            self.assertEqual(objs.bus.read(types['volatile']), 0x050)
            rft.testbench.clock(3)
            self.assertEqual(int(objs.bus.interrupt), 0)
            self.assertEqual(objs.bus.read(types['raw']), 0x000)
            self.assertEqual(objs.bus.read(types['flag']), 0x000)
            self.assertEqual(objs.bus.read(types['status']), 0x000)

            objs.bus.write(types['enable'], 0x555)
            objs.bus.write(types['unmask'], 0x333)
            objs.bus.write(types['pend'], 0xF0F)
            self.assertEqual(objs.bus.read(types['flag']), 0x00F)
            self.assertEqual(objs.bus.read(types['status']), 0x003)
            self.assertEqual(int(objs.bus.interrupt), 1)

            for typ in ['volatile', 'flag', 'pend', 'enable', 'unmask', 'status', 'raw']:
                objs.bus.read(types[typ])
                if typ in ['volatile', 'status', 'raw']:
                    with self.assertRaisesRegex(ValueError, 'decode'):
                        objs.bus.write(types[typ], 0)
                else:
                    objs.bus.write(types[typ], 0)

    def test_errors(self):
        """test interrupt field config errors"""
        base_cfg = {
            'metadata': {'name': 'test'},
            'fields': [
                {
                    'address': 0,
                    'bitrange': 0,
                    'name': 'x',
                    'behavior': 'interrupt-flag',
                    'interrupt': 'x',
                },
            ],
            'interrupts': [
                {
                    'name': 'x',
                },
            ],
        }

        RegisterFileTestbench(base_cfg)

        cfg = deepcopy(base_cfg)
        cfg['fields'][0]['behavior'] = 'interrupt'
        with self.assertRaisesRegex(
                Exception, 'bus cannot access the field; specify a read or '
                'write operation'):
            RegisterFileTestbench(cfg)

        cfg = deepcopy(base_cfg)
        cfg['fields'][0]['bitrange'] = '3..0'
        with self.assertRaisesRegex(
                Exception, 'interrupt fields cannot be vectors, use '
                'repetition instead'):
            RegisterFileTestbench(cfg)

        cfg = deepcopy(base_cfg)
        cfg['fields'][0]['behavior'] = 'interrupt'
        cfg['fields'][0]['mode'] = 'raw'
        cfg['fields'][0]['bus-write'] = 'enabled'
        with self.assertRaisesRegex(
                Exception, 'raw interrupt fields cannot be written'):
            RegisterFileTestbench(cfg)

        cfg = deepcopy(base_cfg)
        cfg['fields'][0]['behavior'] = 'interrupt'
        cfg['fields'][0]['mode'] = 'masked'
        cfg['fields'][0]['bus-write'] = 'enabled'
        with self.assertRaisesRegex(
                Exception, 'masked interrupt fields cannot be written'):
            RegisterFileTestbench(cfg)

        cfg = deepcopy(base_cfg)
        cfg['fields'][0]['behavior'] = 'interrupt'
        cfg['fields'][0]['mode'] = 'masked'
        cfg['fields'][0]['bus-read'] = 'clear'
        with self.assertRaisesRegex(
                Exception, 'only flag interrupt fields support clear-on-read'):
            RegisterFileTestbench(cfg)
