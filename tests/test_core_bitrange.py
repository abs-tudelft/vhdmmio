"""Unit tests for the `vhdmmio.core.bitrange.BitRange` class."""

from unittest import TestCase
from vhdmmio.core.bitrange import BitRange

class TestBitRange(TestCase):
    """Unit tests for the `vhdmmio.core.bitrange.BitRange` class."""

    def test_specs(self):
        """test BitRange specifications"""
        def test(bus_width, spec, *args):
            bitrange = BitRange.from_spec(bus_width, spec)
            self.assertEqual(bitrange, BitRange(bus_width, *args)) #pylint: disable=E1120
            self.assertEqual(bitrange, BitRange.from_spec(bus_width, str(bitrange)))
            self.assertEqual(bitrange, eval(repr(bitrange))) #pylint: disable=W0123

        test(32, 124, 124)
        test(32, '124', 124)
        test(32, '0124', 84)
        test(32, '0b111000/3', 56, 3)
        test(32, '0x34:25', 52, 2, 25)
        test(32, '0x30/4:25..45', 48, 4, 25, 45)
        test(64, '0x30:25..45', 48, 3, 25, 45)
        test(64, ':25..45', 0, 3, 25, 45)
        with self.assertRaisesRegex(ValueError, r'failed to parse address specification'):
            test(64, 'nope')

    def test_cons_and_params(self):
        """test BitRange constructor"""

        bitrange = BitRange(32, 0)
        self.assertEqual(repr(bitrange), 'BitRange(32, 0x00000000)')
        self.assertEqual(bitrange.bus_width, 32)
        self.assertEqual(bitrange.size, 2)

        bitrange = BitRange(64, 0)
        self.assertEqual(repr(bitrange), 'BitRange(64, 0x00000000)')
        self.assertEqual(bitrange.bus_width, 64)
        self.assertEqual(bitrange.size, 3)

        with self.assertRaisesRegex(ValueError, r'invalid bus width'):
            BitRange(24, 0)

        with self.assertRaisesRegex(ValueError, r'not aligned'):
            BitRange(32, 1)

        with self.assertRaisesRegex(ValueError, r'address'):
            BitRange(32, -4)

        with self.assertRaisesRegex(ValueError, r'address'):
            BitRange(32, 0x1000000000)

        with self.assertRaisesRegex(ValueError, r'invalid block size'):
            BitRange(32, 0, 1)

        bitrange = BitRange(32, 0, 2)
        self.assertEqual(repr(bitrange), 'BitRange(32, 0x00000000)')
        self.assertEqual(bitrange.bus_width, 32)
        self.assertEqual(bitrange.size, 2)
        self.assertEqual(bitrange.high_bit, 31)
        self.assertEqual(bitrange.low_bit, 0)
        self.assertEqual(bitrange.width, 32)
        self.assertTrue(bitrange.is_vector())
        self.assertTrue(bitrange.is_word())

        bitrange = BitRange(32, 0, 3)
        self.assertEqual(repr(bitrange), 'BitRange(32, 0x00000000, 3)')
        self.assertEqual(bitrange.bus_width, 32)
        self.assertEqual(bitrange.size, 3)
        self.assertEqual(bitrange.high_bit, 31)
        self.assertEqual(bitrange.low_bit, 0)
        self.assertEqual(bitrange.width, 32)
        self.assertTrue(bitrange.is_vector())
        self.assertTrue(bitrange.is_word())

        with self.assertRaisesRegex(ValueError, r'invalid block size'):
            BitRange(64, 0, 1)

        with self.assertRaisesRegex(ValueError, r'invalid block size'):
            BitRange(64, 0, 2)

        bitrange = BitRange(64, 0, 3)
        self.assertEqual(repr(bitrange), 'BitRange(64, 0x00000000)')
        self.assertEqual(bitrange.bus_width, 64)
        self.assertEqual(bitrange.size, 3)
        self.assertEqual(bitrange.high_bit, 63)
        self.assertEqual(bitrange.low_bit, 0)
        self.assertEqual(bitrange.width, 64)
        self.assertTrue(bitrange.is_vector())
        self.assertTrue(bitrange.is_word())

        bitrange = BitRange(64, 0, 3, 33)
        self.assertEqual(repr(bitrange), 'BitRange(64, 0x00000000, 3, 33)')
        self.assertEqual(bitrange.bus_width, 64)
        self.assertEqual(bitrange.size, 3)
        self.assertEqual(bitrange.high_bit, 33)
        self.assertEqual(bitrange.low_bit, 33)
        self.assertEqual(bitrange.width, 1)
        self.assertFalse(bitrange.is_vector())
        self.assertFalse(bitrange.is_word())

        bitrange = BitRange(64, 0, 3, 33, 22)
        self.assertEqual(repr(bitrange), 'BitRange(64, 0x00000000, 3, 33, 22)')
        self.assertEqual(bitrange.bus_width, 64)
        self.assertEqual(bitrange.size, 3)
        self.assertEqual(bitrange.high_bit, 33)
        self.assertEqual(bitrange.low_bit, 22)
        self.assertEqual(bitrange.width, 12)
        self.assertTrue(bitrange.is_vector())
        self.assertFalse(bitrange.is_word())

        bitrange = BitRange(64, 0, 3, 0, 63)
        self.assertEqual(repr(bitrange), 'BitRange(64, 0x00000000)')
        self.assertEqual(bitrange.bus_width, 64)
        self.assertEqual(bitrange.size, 3)
        self.assertEqual(bitrange.high_bit, 63)
        self.assertEqual(bitrange.low_bit, 0)
        self.assertEqual(bitrange.width, 64)
        self.assertTrue(bitrange.is_vector())
        self.assertTrue(bitrange.is_word())

        with self.assertRaisesRegex(ValueError, r'bit index'):
            BitRange(64, 0, 3, -1)

    def test_iter(self):
        """test iterating over BitRanges"""
        def test(args, *ibre):
            bitrange = BitRange(*args)
            ibr = list(bitrange)
            self.assertEqual(len(bitrange), len(ibr))
            self.assertEqual(ibr, [BitRange.Mapping(*x) for x in ibre])

        #pylint: disable=C0326

        test((32, 24),
             (24,  -4, 31,  0, 31,  0))

        test((32,  24,  2, 10, 96),
             (24,  -4, 31, 10, 21,  0),
             (28,  -4, 31,  0, 53, 22),
             (32,  -4, 31,  0, 85, 54),
             (36,  -4,  0,  0, 86, 86))

        test((32,  24,  2, 10, 95),
             (24,  -4, 31, 10, 21,  0),
             (28,  -4, 31,  0, 53, 22),
             (32,  -4, 31,  0, 85, 54))

        test((32,  24,  2, 10, 96),
             (24,  -4, 31, 10, 21,  0),
             (28,  -4, 31,  0, 53, 22),
             (32,  -4, 31,  0, 85, 54),
             (36,  -4,  0,  0, 86, 86))

        test((32,  24,  2, 31, 95),
             (24,  -4, 31, 31,  0,  0),
             (28,  -4, 31,  0, 32,  1),
             (32,  -4, 31,  0, 64, 33))

        test((32,  24,  2, 32, 95),
             (28,  -4, 31,  0, 31,  0),
             (32,  -4, 31,  0, 63, 32))

        test((32,  16,  4, 32, 95),
             (32, -16, 31,  0, 31,  0),
             (48, -16, 31,  0, 63, 32))

    def test_collections(self):
        """test BitRange sorting and equality"""
        test_set = set()
        test_set.add(BitRange(32, 24, 2, 16))
        test_set.add(BitRange(32, 24, 2, 18))
        test_set.add(BitRange(32, 28, 2, 18))
        test_set.add(BitRange(32, 24, 2, 16, 16))
        test_set.add(BitRange(32, 24, 2, 16))
        test_set.add(BitRange(32, 24, 2, 16, 24))
        self.assertEqual(sorted(test_set), [
            BitRange(32, 24, 2, 16),
            BitRange(32, 24, 2, 16, 16),
            BitRange(32, 24, 2, 16, 24),
            BitRange(32, 24, 2, 18),
            BitRange(32, 28, 2, 18),
        ])
