import itertools
from typing import Any, Iterable

from .monoid import times, combine
from ..types import Record


class Algebraic(Record):
    """
    Wrapper for group/monoid/semigroup data structures.
    """

    algebra: callable
    value: Any

    def __add__(self, other):
        if isinstance(other, Algebraic) and other.algebra is self.algebra:
            return self.wrap(self.algebra(self.value, other.value))
        return NotImplemented

    def __mul__(self, n):
        if isinstance(n, int):
            return self.wrap(times(self.algebra, self.value, n))
        return NotImplemented

    def __rmul__(self, other):
        return self.__mul__(other)

    def __eq__(self, other):
        if isinstance(other, Algebraic):
            return self.value == other.value and self.algebra is other.algebra
        return NotImplemented

    def combine(self, seq: Iterable):
        """
        Combine with sequence.
        """
        seq = itertools.chain([self.value], (x.value for x in seq))
        return self.wrap(combine(self.algebra, seq))

    def wrap(self, x):
        """
        Wrap other value in the same algebra as element.
        """
        return type(self)(self.algebra, x)

    def inv(self):
        """
        Inverse of element.

        Raises a TypeError if algebra does not form a group.
        """
        return self.wrap(self.algebra.inv(self.value))
