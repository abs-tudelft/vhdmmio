"""Submodule for dealing with expression synthesis."""

import re
from collections import OrderedDict

class LinearExpression:
    """Object that abstracts a linear integer expression of terms in a foreign
    language (i.e. VHDL) represented as strings. Overrides basic math operators
    to modify the expression in such a way that the resulting expression string
    does not explode with parentheses."""

    def __init__(self, *args):
        """Constructs a linear expression from one of the following:

         - nothing: returns 0.
         - a string: interprets the string as a foreign expression.
         - an integer: used as offset.
         - another linear expression: constructs a copy.
         - a tuple of terms and an offset: constructs an expression from those.
        """
        super().__init__()
        if not args:
            self._terms = ()
            self._offset = 0
            return
        if len(args) == 2:
            self._terms, self._offset = args
            return
        if len(args) == 1:
            if isinstance(args[0], str):
                self._terms = (self._term_from_expr(args[0]),)
                self._offset = 0
                return
            if isinstance(args[0], int):
                self._terms = ()
                self._offset = args[0]
                return
            if isinstance(args[0], LinearExpression):
                self._terms = args[0].terms
                self._offset = args[0].offset
                return
        raise TypeError('cannot convert to linear expression: %r' % args)

    @property
    def terms(self):
        """Returns the terms as a tuple of (factor, expression) two-tuples."""
        return self._terms

    @property
    def offset(self):
        """Returns the integer offset."""
        return self._offset

    @staticmethod
    def _term_from_expr(expression, factor=1):
        if re.match(r'[a-zA-Z0-9_]+$|\(.*\)$', expression):
            fmt = '%s'
        else:
            fmt = '(%s)'
        return (factor, fmt % expression)

    def __add__(self, other):
        other = LinearExpression(other)
        terms = OrderedDict()
        for factor, expression in self.terms + other.terms:
            if expression in terms:
                terms[expression] += factor
            else:
                terms[expression] = factor
        terms = tuple(((factor, expression) for expression, factor in terms.items()))
        return LinearExpression(terms, self.offset + other.offset)

    __radd__ = __add__

    def __sub__(self, other):
        return self + (-LinearExpression(other))

    def __rsub__(self, other):
        return (-self) + other

    def __mul__(self, other):
        if not isinstance(other, int):
            raise TypeError('unsupported type %s' % type(other).__name__)
        if other == 0:
            return LinearExpression()
        return LinearExpression(
            tuple(((f * other, e) for f, e in self.terms)),
            self.offset * other)

    __rmul__ = __mul__

    def __neg__(self):
        return self * -1

    def __pos__(self):
        return self

    def __str__(self):
        terms = []
        for factor, expression in self.terms:
            if factor > 1:
                term = ' + %d*%s' % (factor, expression)
            elif factor == 1:
                term = ' + %s' % (expression)
            elif factor == 0:
                continue
            elif factor == -1:
                term = ' - %s' % (expression)
            else:
                term = ' - %d*%s' % (-factor, expression)
            terms.append(term)
        if self.offset > 0:
            terms.append(' + %d' % self.offset)
        elif self.offset < 0:
            terms.append(' - %d' % (-self.offset))
        if not terms:
            return '0'
        first, *others = terms
        if first.startswith(' + '):
            first = first[3:]
        elif first.startswith(' - '):
            first = '-' + first[3:]
        return first + ''.join(others)


def expr(*args):
    """Shorthand for constructing linear expressions."""
    if len(args) == 1 and isinstance(args[0], LinearExpression):
        return args[0]
    return LinearExpression(*args)
