"""Tests for the classes defined in `vhdmmio.core.address`."""

from collections import OrderedDict
from unittest import TestCase
from vhdmmio.core.mixins import Shaped, Named, Unique
from vhdmmio.core.address import AddressSignalMap, MaskedAddress, AddressManager

class Signal(Shaped, Named, Unique):
    """Generic `Shaped+Named+Unique` class for testing purposes."""

def add_mapping(mgr, obj, bus_address, read=True, write=True, conditions=None):
    """Adds a mapping for obj with the specified read/write mode.
    `conditions` should be a mapping object from `Shaped+Named+Unique`
    signal objects to `MaskedAddress` objects if specified."""
    subaddresses = {AddressSignalMap.BUS: bus_address}
    if conditions is not None:
        subaddresses.update(conditions)
    address = mgr.signals.construct_address(subaddresses)
    if read:
        mgr.read_map(address, lambda: obj)
    if write:
        mgr.write_map(address, lambda: obj)


class TestAddresses(TestCase):
    """Tests for the classes defined in `vhdmmio.core.address`."""

    def test_subsequent(self):
        """test the masked adder logic for finding subsequent blocks"""
        # Adding:
        #     0b01011010
        #     0b01101100
        #  (C=0b11110000)
        #     ---------- +
        #     0b11000110
        addr = MaskedAddress.parse_config('0b0-1--0--11--0-10')
        addr += 0b01101100
        self.assertEqual(addr, MaskedAddress.parse_config('0b1-1--0--00--1-10'))

    def test_16550(self):
        """test an AddressManager with 16550's DLAB madness"""
        self.maxDiff = None #pylint: disable=C0103
        dlab = Signal(name='dlab')
        mgr = AddressManager()
        add_mapping(mgr, 'RBR', MaskedAddress(0, 0xFFFFFFFF), 1, 0, {dlab: MaskedAddress(0, 1)})
        add_mapping(mgr, 'THR', MaskedAddress(0, 0xFFFFFFFF), 0, 1, {dlab: MaskedAddress(0, 1)})
        add_mapping(mgr, 'IER', MaskedAddress(1, 0xFFFFFFFF), 1, 1, {dlab: MaskedAddress(0, 1)})
        add_mapping(mgr, 'ISR', MaskedAddress(2, 0xFFFFFFFF), 1, 0)
        add_mapping(mgr, 'FCR', MaskedAddress(2, 0xFFFFFFFF), 0, 1)
        add_mapping(mgr, 'LCR', MaskedAddress(3, 0xFFFFFFFF), 1, 1)
        add_mapping(mgr, 'MCR', MaskedAddress(4, 0xFFFFFFFF), 1, 1)
        add_mapping(mgr, 'LSR', MaskedAddress(5, 0xFFFFFFFF), 1, 1)
        add_mapping(mgr, 'MSR', MaskedAddress(6, 0xFFFFFFFE), 1, 1)
        add_mapping(mgr, 'DLL', MaskedAddress(0, 0xFFFFFFFF), 1, 1, {dlab: MaskedAddress(1, 1)})
        add_mapping(mgr, 'DLH', MaskedAddress(1, 0xFFFFFFFF), 1, 1, {dlab: MaskedAddress(1, 1)})
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
            add_mapping(mgr, 'SPR', MaskedAddress(7, 0xFFFFFFFF), 1, 1)
