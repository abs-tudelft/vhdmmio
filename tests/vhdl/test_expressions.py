"""Tests for the VHDL expression abstraction submodule."""

from unittest import TestCase
from vhdmmio.vhdl.expressions import expr

class TestVhdlExpressions(TestCase):
    """Tests for the VHDL expression abstraction submodule."""

    def test_constant(self):
        """test constant VHDL expressions"""
        self.assertEqual(str(expr(expr())), '0')
        self.assertEqual(str(expr(-2)), '-2')
        self.assertEqual(str(expr(-1)), '-1')
        self.assertEqual(str(expr(0)), '0')
        self.assertEqual(str(expr(1)), '1')
        self.assertEqual(str(expr(2)), '2')
        self.assertEqual(str(expr(2) + 3), '5')
        self.assertEqual(str(expr(2) - 3), '-1')
        self.assertEqual(str(2 - expr(3)), '-1')
        self.assertEqual(str(expr(2) * 3), '6')
        self.assertEqual(str(expr(2) * 0), '0')
        self.assertEqual(str(-expr(2)), '-2')
        self.assertEqual(str(+expr(2)), '2')

    def test_foreign(self):
        """test VHDL expressions with one foreign component"""
        #pylint: disable=E1130
        self.assertEqual(str(expr('2')), '2')
        self.assertEqual(str(expr('hello')), 'hello')
        self.assertEqual(str(expr('foo + bar')), '(foo + bar)')
        self.assertEqual(str(expr('a') + 3), 'a + 3')
        self.assertEqual(str(expr('a') - 3), 'a - 3')
        self.assertEqual(str(2 - expr('a')), '-a + 2')
        self.assertEqual(str(expr('a') * 3), '3*a')
        self.assertEqual(str(expr('a') * -3), '-3*a')
        self.assertEqual(str(expr('a') * 0), '0')
        self.assertEqual(str(-expr('a')), '-a')
        self.assertEqual(str(+expr('a')), 'a')

    def test_multiple_foreign(self):
        """test VHDL expressions with two foreign components"""
        self.assertEqual(str(expr('a') + 'b'), 'a + b')
        self.assertEqual(str(expr('a') - 'a'), '0')
        self.assertEqual(str(expr('a') + expr('b') + expr('a')), '2*a + b')

    def test_typecheck(self):
        """test VHDL expression construction type checks"""
        with self.assertRaises(TypeError):
            expr() * expr() #pylint: disable=W0106
        with self.assertRaises(TypeError):
            expr(2, 2, 2)
        with self.assertRaises(TypeError):
            expr(None)
