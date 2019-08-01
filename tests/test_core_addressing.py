"""Tests for the classes defined in `vhdmmio.core.addressing`."""

from collections import OrderedDict
from unittest import TestCase
from vhdmmio.core.mixins import Shaped, Named, Unique
from vhdmmio.core.addressing import AddressSignalMap, MaskedAddress, AddressManager

class Signal(Shaped, Named, Unique):
    """Generic `Shaped+Named+Unique` class for testing purposes."""

class TestAddressing(TestCase):
    """Tests for the classes defined in `vhdmmio.core.addressing`."""

    def test_16550(self):
        """test an AddressManager with 16550's DLAB madness"""
        self.maxDiff = None #pylint: disable=C0103
        dlab = Signal(name='dlab')
        mgr = AddressManager()
        mgr.add_mapping('RBR', MaskedAddress(0, 0xFFFFFFFF), 1, 0, {dlab: MaskedAddress(0, 1)})
        mgr.add_mapping('THR', MaskedAddress(0, 0xFFFFFFFF), 0, 1, {dlab: MaskedAddress(0, 1)})
        mgr.add_mapping('IER', MaskedAddress(1, 0xFFFFFFFF), 1, 1, {dlab: MaskedAddress(0, 1)})
        mgr.add_mapping('ISR', MaskedAddress(2, 0xFFFFFFFF), 1, 0)
        mgr.add_mapping('FCR', MaskedAddress(2, 0xFFFFFFFF), 0, 1)
        mgr.add_mapping('LCR', MaskedAddress(3, 0xFFFFFFFF), 1, 1)
        mgr.add_mapping('MCR', MaskedAddress(4, 0xFFFFFFFF), 1, 1)
        mgr.add_mapping('LSR', MaskedAddress(5, 0xFFFFFFFF), 1, 1)
        mgr.add_mapping('MSR', MaskedAddress(6, 0xFFFFFFFE), 1, 1)
        mgr.add_mapping('DLL', MaskedAddress(0, 0xFFFFFFFF), 1, 1, {dlab: MaskedAddress(1, 1)})
        mgr.add_mapping('DLH', MaskedAddress(1, 0xFFFFFFFF), 1, 1, {dlab: MaskedAddress(1, 1)})
        self.assertEqual(list(mgr.doc_iter()), [
            (
                OrderedDict((
                    (AddressSignalMap.BUS, MaskedAddress(0, 0xFFFFFFFF)),
                    (dlab, MaskedAddress(0, 1)))),
                '0x00000000, `dlab`=0',
                'RBR', 'THR'
            ),
            (
                OrderedDict((
                    (AddressSignalMap.BUS, MaskedAddress(0, 0xFFFFFFFF)),
                    (dlab, MaskedAddress(1, 1)))),
                '0x00000000, `dlab`=1',
                'DLL', 'DLL'
            ),
            (
                OrderedDict((
                    (AddressSignalMap.BUS, MaskedAddress(1, 0xFFFFFFFF)),
                    (dlab, MaskedAddress(0, 1)))),
                '0x00000001, `dlab`=0',
                'IER', 'IER'
            ),
            (
                OrderedDict((
                    (AddressSignalMap.BUS, MaskedAddress(1, 0xFFFFFFFF)),
                    (dlab, MaskedAddress(1, 1)))),
                '0x00000001, `dlab`=1',
                'DLH', 'DLH'
            ),
            (
                OrderedDict((
                    (AddressSignalMap.BUS, MaskedAddress(2, 0xFFFFFFFF)),
                    (dlab, MaskedAddress(0, 0)))),
                '0x00000002',
                'ISR', 'FCR'
            ),
            (
                OrderedDict((
                    (AddressSignalMap.BUS, MaskedAddress(3, 0xFFFFFFFF)),
                    (dlab, MaskedAddress(0, 0)))),
                '0x00000003',
                'LCR', 'LCR'
            ),
            (
                OrderedDict((
                    (AddressSignalMap.BUS, MaskedAddress(4, 0xFFFFFFFF)),
                    (dlab, MaskedAddress(0, 0)))),
                '0x00000004',
                'MCR', 'MCR'
            ),
            (
                OrderedDict((
                    (AddressSignalMap.BUS, MaskedAddress(5, 0xFFFFFFFF)),
                    (dlab, MaskedAddress(0, 0)))),
                '0x00000005',
                'LSR', 'LSR'
            ),
            (
                OrderedDict((
                    (AddressSignalMap.BUS, MaskedAddress(6, 0xFFFFFFFE)),
                    (dlab, MaskedAddress(0, 0)))),
                '0x00000006/1',
                'MSR', 'MSR'
            )])
        with self.assertRaisesRegex(
                ValueError, r'address conflict between SPR \(0x00000007\) and '
                r'MSR \(0x00000006/1\) at 0x00000007, `dlab`=0 in read mode'):
            mgr.add_mapping('SPR', MaskedAddress(7, 0xFFFFFFFF), 1, 1)
