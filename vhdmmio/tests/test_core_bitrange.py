from unittest import TestCase
import os
import tempfile

import vhdmmio
from vhdmmio.core.bitrange import *

class TestBitRange(TestCase):

    def test_specs(self):
        def test(bus_width, spec, *args):
            br = BitRange.from_spec(bus_width, spec)
            self.assertEquals(br, BitRange(bus_width, *args))
            self.assertEquals(br, BitRange.from_spec(bus_width, str(br)))
            self.assertEquals(br, eval(repr(br)))

        test(32, 124, 124)
        test(32, '124', 124)
        test(32, '0124', 84)
        test(32, '0b111000/3', 56, 3)
        test(32, '0x34:25', 52, 2, 25)
        test(32, '0x30/4:25..45', 48, 4, 25, 45)
        test(64, '0x30:25..45', 48, 3, 25, 45)
        with self.assertRaisesRegex(ValueError, r'failed to parse address specification'):
            test(64, 'nope')

    def test_cons_and_params(self):

        br = BitRange(32, 0)
        self.assertEquals(repr(br), 'BitRange(32, 0x00000000)')
        self.assertEquals(br.bus_width, 32)
        self.assertEquals(br.size, 2)

        br = BitRange(64, 0)
        self.assertEquals(repr(br), 'BitRange(64, 0x00000000)')
        self.assertEquals(br.bus_width, 64)
        self.assertEquals(br.size, 3)

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

        br = BitRange(32, 0, 2)
        self.assertEquals(repr(br), 'BitRange(32, 0x00000000)')
        self.assertEquals(br.bus_width, 32)
        self.assertEquals(br.size, 2)
        self.assertEquals(br.high_bit, 31)
        self.assertEquals(br.low_bit, 0)
        self.assertEquals(br.width, 32)
        self.assertTrue(br.is_vector())
        self.assertTrue(br.is_word())

        br = BitRange(32, 0, 3)
        self.assertEquals(repr(br), 'BitRange(32, 0x00000000, 3)')
        self.assertEquals(br.bus_width, 32)
        self.assertEquals(br.size, 3)
        self.assertEquals(br.high_bit, 31)
        self.assertEquals(br.low_bit, 0)
        self.assertEquals(br.width, 32)
        self.assertTrue(br.is_vector())
        self.assertTrue(br.is_word())

        with self.assertRaisesRegex(ValueError, r'invalid block size'):
            BitRange(64, 0, 1)

        with self.assertRaisesRegex(ValueError, r'invalid block size'):
            BitRange(64, 0, 2)

        br = BitRange(64, 0, 3)
        self.assertEquals(repr(br), 'BitRange(64, 0x00000000)')
        self.assertEquals(br.bus_width, 64)
        self.assertEquals(br.size, 3)
        self.assertEquals(br.high_bit, 63)
        self.assertEquals(br.low_bit, 0)
        self.assertEquals(br.width, 64)
        self.assertTrue(br.is_vector())
        self.assertTrue(br.is_word())

        br = BitRange(64, 0, 3, 33)
        self.assertEquals(repr(br), 'BitRange(64, 0x00000000, 3, 33)')
        self.assertEquals(br.bus_width, 64)
        self.assertEquals(br.size, 3)
        self.assertEquals(br.high_bit, 33)
        self.assertEquals(br.low_bit, 33)
        self.assertEquals(br.width, 1)
        self.assertFalse(br.is_vector())
        self.assertFalse(br.is_word())

        br = BitRange(64, 0, 3, 33, 22)
        self.assertEquals(repr(br), 'BitRange(64, 0x00000000, 3, 33, 22)')
        self.assertEquals(br.bus_width, 64)
        self.assertEquals(br.size, 3)
        self.assertEquals(br.high_bit, 33)
        self.assertEquals(br.low_bit, 22)
        self.assertEquals(br.width, 12)
        self.assertTrue(br.is_vector())
        self.assertFalse(br.is_word())

        br = BitRange(64, 0, 3, 0, 63)
        self.assertEquals(repr(br), 'BitRange(64, 0x00000000)')
        self.assertEquals(br.bus_width, 64)
        self.assertEquals(br.size, 3)
        self.assertEquals(br.high_bit, 63)
        self.assertEquals(br.low_bit, 0)
        self.assertEquals(br.width, 64)
        self.assertTrue(br.is_vector())
        self.assertTrue(br.is_word())

        with self.assertRaisesRegex(ValueError, r'bit index'):
            BitRange(64, 0, 3, -1)

    def test_iter(self):
        def test(args, *ibre):
            br = BitRange(*args)
            ibr = list(br)
            self.assertEquals(len(br), len(ibr))
            self.assertEquals(ibr, [BitRange.Mapping(*x) for x in ibre])

        test((32, 24),
             (24, -4, 31,  0, 31,  0))

        test((32, 24, 2, 10, 96),
             (24, -4, 31, 10, 21,  0),
             (28, -4, 31,  0, 53, 22),
             (32, -4, 31,  0, 85, 54),
             (36, -4,  0,  0, 86, 86))

        test((32, 24, 2, 10, 95),
             (24, -4, 31, 10, 21,  0),
             (28, -4, 31,  0, 53, 22),
             (32, -4, 31,  0, 85, 54))

        test((32, 24, 2, 10, 96),
             (24, -4, 31, 10, 21,  0),
             (28, -4, 31,  0, 53, 22),
             (32, -4, 31,  0, 85, 54),
             (36, -4,  0,  0, 86, 86))

        test((32, 24, 2, 31, 95),
             (24, -4, 31, 31, 0,  0),
             (28, -4, 31,  0, 32, 1),
             (32, -4, 31,  0, 64, 33))

        test((32, 24, 2, 32, 95),
             (28, -4, 31,  0, 31, 0),
             (32, -4, 31,  0, 63, 32))

        test((32, 16, 4, 32, 95),
             (32, -16, 31,  0, 31, 0),
             (48, -16, 31,  0, 63, 32))

    def test_collections(self):
        x = set()
        x.add(BitRange(32, 24, 2, 16))
        x.add(BitRange(32, 24, 2, 18))
        x.add(BitRange(32, 28, 2, 18))
        x.add(BitRange(32, 24, 2, 16, 16))
        x.add(BitRange(32, 24, 2, 16))
        x.add(BitRange(32, 24, 2, 16, 24))
        self.assertEquals(sorted(x), [
            BitRange(32, 24, 2, 16),
            BitRange(32, 24, 2, 16, 16),
            BitRange(32, 24, 2, 16, 24),
            BitRange(32, 24, 2, 18),
            BitRange(32, 28, 2, 18),
        ])
