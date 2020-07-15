import functools
import itertools

from .wrapper import Algebraic
from ..functions import fn


class semigroup(fn):
    """
    A semigroup decorator.
    """

    @classmethod
    def wrap(cls, x):
        return Algebraic(cls, x)

    @classmethod
    def from_operator(cls, op, **kwargs):
        return cls(lambda *args: functools.reduce(op, args))

    @property
    def __sk_callable__(self):
        return self

    def __new__(cls, func=None, **kwargs):
        if func is None:
            return lambda f: cls(f, **kwargs)
        return super().__new__(cls, func)

    def __init__(self, func=None, combine=None):
        super().__init__(func)
        if combine:
            self.combine = combine

    def combine(self, seq):
        """
        Combine sequence of elements of semigroup.

        Empty sequences raises ValueErrors.
        """
        op = self._func
        seq = iter(seq)
        x = op(*itertools.islice(seq, 32))
        while seq:
            x = op(x, op(*itertools.islice(seq, 32)))
        return x


def concatenation_semigroup(constructor):
    """
    Create a semigroup function that builds objects by concatenation from the
    given constructor.

    If constructor accepts empty sequences (as it happens in most cases), it
    also defines a monoid.
    """
    return semigroup(lambda *args: constructor(itertools.chain.from_iterable(args)))
