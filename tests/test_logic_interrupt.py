"""Tests for interrupt fields and derivatives."""

from unittest import TestCase
from .testbench import RegisterFileTestbench

class TestInterrupt(TestCase):
    """Tests for primitive fields and derivatives."""

    def test_interrupt(self):
        """test interrupt fields"""

        # irq_a (0): scalar interrupt with all registers
        # irq_b (1): scalar interrupt without enable register
        # irq_c (2): scalar interrupt without unmask register
        # irq_d (3): scalar interrupt without clear/pend
        # irq_e (7..4): vector interrupt with all registers

        def gen_fields(name, irqs):
            fields = []
            if 'a' in irqs:
                fields.append({
                    'register-name': name,
                    'address': '0:0',
                    'name': '%s_a' % name,
                    'interrupt': 'irq_a',
                })
            if 'b' in irqs:
                fields.append({
                    'address': '0:1',
                    'name': '%s_b' % name,
                    'interrupt': 'irq_b',
                })
            if 'c' in irqs:
                fields.append({
                    'address': '0:2',
                    'name': '%s_c' % name,
                    'interrupt': 'irq_c',
                })
            if 'd' in irqs:
                fields.append({
                    'address': '0:3',
                    'name': '%s_d' % name,
                    'interrupt': 'irq_d',
                })
            if 'e' in irqs:
                fields.append({
                    'address': '0:4',
                    'repeat': 4,
                    'name': '%s_e' % name,
                    'interrupt': 'irq_e',
                })
            return fields

        rft = RegisterFileTestbench({
            'meta': {'name': 'test'},
            'features': {'bus-width': 32, 'optimize': False},
            'interface': {'port-flatten': True},
            'interrupts': [
                {'name': 'irq_a'},
                {'name': 'irq_b'},
                {'name': 'irq_c'},
                {'name': 'irq_d'},
                {'name': 'irq_e', 'width': 4},
            ],
            'fields': [
                {
                    'base': 0,
                    'type': 'interrupt-flag',
                    'subfields': gen_fields('flag', 'abce')
                },
                {
                    'base': 4,
                    'type': 'interrupt-flag',
                    'read': 'disabled',
                    'subfields': gen_fields('flag_wo', 'abce')
                },
                {
                    'base': 8,
                    'type': 'interrupt-flag',
                    'write': 'disabled',
                    'subfields': gen_fields('flag_ro', 'abcde')
                },
                {
                    'base': 12,
                    'type': 'volatile-interrupt-flag',
                    'subfields': gen_fields('flag_vol', 'abce')
                },
                {
                    'base': 16,
                    'type': 'interrupt-pend',
                    'subfields': gen_fields('pend', 'abce')
                },
                {
                    'base': 20,
                    'type': 'interrupt-enable',
                    'subfields': gen_fields('enable', 'acde')
                },
                {
                    'base': 24,
                    'type': 'interrupt-enable',
                    'write': 'set',
                    'subfields': gen_fields('set_enable', 'acde')
                },
                {
                    'base': 28,
                    'type': 'interrupt-enable',
                    'write': 'clear',
                    'read': 'disabled',
                    'subfields': gen_fields('clear_enable', 'acde')
                },
                {
                    'base': 32,
                    'type': 'interrupt-unmask',
                    'subfields': gen_fields('unmask', 'abde')
                },
                {
                    'base': 36,
                    'type': 'interrupt-status',
                    'subfields': gen_fields('status', 'abcde')
                },
                {
                    'base': 40,
                    'type': 'interrupt-raw',
                    'subfields': gen_fields('raw', 'abcde')
                },
            ]
        })
        with rft as objs:

            # Test interrupt-flag and interrupt-pend field.
            self.assertEqual(objs.bus.read(0), 0x00)
            objs.bus.write(16, 0xFF)
            self.assertEqual(objs.bus.read(0), 0xF7)
            objs.bus.write(0, 0x33)
            self.assertEqual(objs.bus.read(0), 0xC4)
            objs.bus.write(0, 0xFF)
            self.assertEqual(objs.bus.read(0), 0x00)

            # Test read-only and write-only interrupt-flag field.
            with self.assertRaisesRegex(ValueError, 'decode error'):
                self.assertEqual(objs.bus.read(4), 0)
            with self.assertRaisesRegex(ValueError, 'decode error'):
                objs.bus.write(8, 0x00)
            objs.bus.write(16, 0xFF)
            self.assertEqual(objs.bus.read(8), 0xF7)
            objs.bus.write(4, 0x33)
            self.assertEqual(objs.bus.read(8), 0xC4)
            objs.bus.write(4, 0xFF)
            self.assertEqual(objs.bus.read(8), 0x00)

            # Test volatile-interrupt-flag field.
            self.assertEqual(objs.bus.read(12), 0x00)
            objs.bus.write(16, 0xFF)
            self.assertEqual(objs.bus.read(12), 0xF7)
            self.assertEqual(objs.bus.read(12), 0x00)

            # Test interrupt-enable field.
            self.assertEqual(objs.bus.read(20), 0x00)
            objs.bus.write(20, 0xFF)
            self.assertEqual(objs.bus.read(20), 0xFD)
            objs.bus.write(20, 0x33)
            self.assertEqual(objs.bus.read(20), 0x31)
            objs.bus.write(20, 0x00)

            # Test interrupt-enable field, set and clear mode.
            self.assertEqual(objs.bus.read(24), 0x00)
            objs.bus.write(24, 0x33)
            self.assertEqual(objs.bus.read(24), 0x31)
            objs.bus.write(24, 0x66)
            self.assertEqual(objs.bus.read(24), 0x75)
            objs.bus.write(24, 0x00)
            self.assertEqual(objs.bus.read(24), 0x75)
            objs.bus.write(28, 0x00)
            self.assertEqual(objs.bus.read(24), 0x75)
            objs.bus.write(28, 0x33)
            self.assertEqual(objs.bus.read(24), 0x44)
            objs.bus.write(28, 0x66)
            self.assertEqual(objs.bus.read(24), 0x00)

            # Test interrupt-unmask field.
            self.assertEqual(objs.bus.read(32), 0x00)
            objs.bus.write(32, 0xFF)
            self.assertEqual(objs.bus.read(32), 0xFB)
            objs.bus.write(32, 0x33)
            self.assertEqual(objs.bus.read(32), 0x33)
            objs.bus.write(32, 0x00)

            # Test edge-sensitive interrupt logic along with status and raw
            # registers.
            def check(request, flag, status, output):
                objs.i_irq_a_request.val = bool(request & 1)
                objs.i_irq_b_request.val = bool(request & 2)
                objs.i_irq_c_request.val = bool(request & 4)
                objs.i_irq_d_request.val = bool(request & 8)
                objs.i_irq_e_request.val = request >> 4
                rft.testbench.clock()
                self.assertEqual(objs.bus.read(40), request)
                self.assertEqual(objs.bus.read(8), flag)
                self.assertEqual(objs.bus.read(36), status)
                self.assertEqual(int(objs.bus.interrupt), output)

            # Edge-sensitive interrupt with enable and unmask.
            check(0x01, 0x00, 0x00, 0)
            check(0x00, 0x00, 0x00, 0)
            objs.bus.write(20, 0x01)
            check(0x00, 0x00, 0x00, 0)
            check(0x01, 0x01, 0x00, 0)
            check(0x00, 0x01, 0x00, 0)
            objs.bus.write(20, 0x00)
            check(0x00, 0x01, 0x00, 0)
            objs.bus.write(32, 0x01)
            check(0x00, 0x01, 0x01, 1)
            objs.bus.write(0, 0x01)
            check(0x00, 0x00, 0x00, 0)

            # Edge-sensitive interrupt with only unmask.
            check(0x02, 0x02, 0x00, 0)
            check(0x00, 0x02, 0x00, 0)
            objs.bus.write(32, 0x02)
            check(0x00, 0x02, 0x02, 1)
            objs.bus.write(0, 0x02)
            check(0x00, 0x00, 0x00, 0)

            # Edge-sensitive interrupt with only enable.
            check(0x04, 0x00, 0x00, 0)
            check(0x00, 0x00, 0x00, 0)
            objs.bus.write(20, 0x04)
            check(0x00, 0x00, 0x00, 0)
            check(0x04, 0x04, 0x04, 1)
            check(0x00, 0x04, 0x04, 1)
            objs.bus.write(20, 0x00)
            check(0x00, 0x04, 0x04, 1)
            objs.bus.write(0, 0x04)
            check(0x00, 0x00, 0x00, 0)

            # Level-sensitive interrupt with enable and unmask.
            check(0x08, 0x00, 0x00, 0)
            check(0x00, 0x00, 0x00, 0)
            objs.bus.write(20, 0x08)
            check(0x08, 0x08, 0x00, 0)
            check(0x00, 0x00, 0x00, 0)
            objs.bus.write(20, 0x00)
            objs.bus.write(32, 0x08)
            check(0x08, 0x00, 0x00, 0)
            check(0x00, 0x00, 0x00, 0)
            objs.bus.write(20, 0x08)
            check(0x08, 0x08, 0x08, 1)
            check(0x00, 0x00, 0x00, 0)
