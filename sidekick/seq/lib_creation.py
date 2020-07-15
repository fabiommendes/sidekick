import itertools
from collections import deque
from numbers import Real

from .iter import generator, Iter
from .util import to_index_seq, INDEX_DOC
from ..functions import fn, to_callable
from ..typing import Seq, TYPE_CHECKING, T, Callable, Index

if TYPE_CHECKING:
    from .. import api as sk  # noqa: F401
    from ..api import X, Y  # noqa: F401


@fn.curry(1)
def cycle(seq, n=None):
    """
    Return elements from the iterable until it is exhausted.
    Then repeat the sequence indefinitely.

        cycle(seq) ==> seq[0], seq[1], ..., seq[n - 1], seq[0], seq[1], ...

    Args:
        seq:
            Input sequence.
        n:
            Optional maximum number of cycles.

    Examples:
        >>> sk.cycle([1, 2, 3])
        sk.iter([1, 2, 3, 1, 2, 3, ...])
    """
    if n is not None:
        return Iter(_ncycle(n, seq))
    return Iter(itertools.cycle(seq))


# This implementation accepts infinite sequences
def _ncycle(n, seq):
    buf = []
    add = buf.append
    for x in seq:
        yield x
        add(x)
    yield from itertools.chain.from_iterable(repeat(buf, n - 1))


@fn.curry(1)
def repeat(obj, times=None):
    """
    Returns the object for the specified number of times.

    If not specified, returns the object endlessly.

    Examples:
        >>> sk.repeat(42, times=5)
        sk.iter([42, 42, 42, 42, 42])
    """
    return Iter(itertools.repeat(obj, times))


@fn
@generator
def repeatedly(func, *args, **kwargs):
    """
    Make infinite calls to a function with the given arguments.

    End sequence if func() raises StopIteration.

    Examples:
        >>> sk.repeatedly(list, (1, 2))
        sk.iter([[1, 2], [1, 2], [1, 2], [1, 2], [1, 2], ...])
    """
    func = to_callable(func)
    try:
        while True:
            yield func(*args, **kwargs)
    except StopIteration as e:
        yield from stop_seq(e)


@fn
@generator
def singleton(obj: T, expand: bool = False) -> Iter[T]:
    """
    Return iterator with a single object.

    Args:
        obj:
            Single element of sequence.
        expand:
            If True, return elements of object if it is iterable or wrap it into
            a singleton iterator if it is not.

    Examples:
        >>> sk.singleton(42)
        sk.iter([42])
    """
    if expand:
        try:
            yield from obj
        except TypeError:
            pass
    yield obj


@fn.curry(2)
@generator
def unfold(func, seed):
    """
    Invert a fold.

    Similar to iterate, but expects a function of seed -> (seed', x). The second
    value of the tuple is included in the resulting sequence while the first
    is used to seed func in the next iteration. Stops iteration if func returns
    None or raise StopIteration.

    Examples:
        >>> sk.unfold(lambda x: (x + 1, x), 0)
        sk.iter([0, 1, 2, 3, 4, 5, ...])
    """
    try:
        elem = func(seed)
        while elem is not None:
            seed, x = elem
            yield x
            elem = func(seed)
    except StopIteration as e:
        yield from stop_seq(e)


@fn.curry(2)
def iterate(func: Callable[..., T], x: T, *args, index: Index = None):
    f"""
    Repeatedly apply a function func to input.

    If more than one argument to func is passed, it iterate over the past n
    values. It requires at least one argument, if you need to iterate a zero
    argument function, call :func:`repeatedly`

    Iteration stops if if func() raise StopIteration.

        iterate(f, x) ==> x, f(x), f(f(x)), ...

    Args:
        func:
            Iterating function. Compute the next element by calling func(prev).
        x:
            Seed of iteration. If more arguments are given, pass them to func
            to compute the next element.
        {INDEX_DOC}

    Examples:
        Simple usage, with a single argument. Produces powers of two.

        >>> sk.iterate((X * 2), 1)
        sk.iter([1, 2, 4, 8, 16, 32, ...])

        Fibonacci numbers

        >>> sk.iterate((X + Y), 1, 1)
        sk.iter([1, 1, 2, 3, 5, 8, ...])

        Factorials

        >>> sk.iterate(op.mul, 1, index=1)
        sk.iter([1, 1, 2, 6, 24, 120, ...])

        Collatz sequence

        >>> @sk.iterate
        ... def collatz(n):
        ...     if n == 1:
        ...         raise StopIteration(1)
        ...     elif n % 2:
        ...         return 3 * n + 1
        ...     else:
        ...         return n // 2
        >>> collatz(10)
        sk.iter([10, 5, 16, 8, 4, 2, ...])

    See Also:
        :func:`repeatedly` - call function with the same arguments.
    """
    func = to_callable(func)
    index = to_index_seq(index)

    if index is None and not args:
        out = _iterate(func, x)
    elif index is None:
        out = _iterate_n(func, (x, *args))
    else:
        if not args:
            out = _iterate_indexed(func, index, x)
        else:
            out = _iterate_indexed_n(func, index, (x, *args))

    return Iter(out)


def _iterate(func, x):
    try:
        yield x
        while True:
            x = func(x)
            yield x
    except StopIteration as e:
        yield from stop_seq(e)


def _iterate_n(func, args):
    n = len(args)
    try:
        yield from args
        if n == 2:
            x, y = args
            while True:
                x, y = y, func(x, y)
                yield y
        else:
            args = deque(args, n)
            while True:
                new = func(*args)
                args.append(new)
                yield new
    except StopIteration as e:
        yield from stop_seq(e)


def _iterate_indexed(func, index, x):
    try:
        yield x
        for i in index:
            x = func(i, x)
            yield x
    except StopIteration as e:
        yield from stop_seq(e)


def _iterate_indexed_n(func, index, args):
    n = len(args)
    try:
        yield from args
        if n == 2:
            x, y = args
            for i in index:
                x, y = y, func(i, x, y)
                yield y
        else:
            args = deque(args, n)
            for i in index:
                new = func(i, *args)
                args.append(new)
                yield new
    except StopIteration as e:
        yield from stop_seq(e)


class _nums(fn):
    """
    Enrich the nums() function.
    """

    def __getitem__(self, item):
        if isinstance(item, tuple):
            return self.from_sequence(item)
        elif isinstance(item, slice):
            return self.from_slice(item)
        else:
            raise TypeError

    def __iter__(self):
        return Iter(itertools.count())

    def from_sequence(self, seq):
        """
        Create iterator from sequence of numbers.
        """
        return Iter(self._from_sequence(seq))

    def _from_sequence(self, seq):
        if len(seq) < 2:
            raise ValueError("sequence must have at least 2 elements")

        idx = seq.index(...)
        if idx == 0:
            raise ValueError("range cannot start with an ellipsis")

        idx_ = idx - len(seq)

        if idx_ == -1:
            n_args = len(seq)
            if n_args == 2:
                yield from itertools.count(seq[0])
            else:
                *start, a, b, _ = seq
                yield from start
                yield from itertools.count(a, b - a)

        elif idx_ == -2:
            n_args = len(seq)
            if n_args == 3:
                a, _, stop = seq
                step = 1
            else:
                *start, a, b, _, stop = seq
                step = b - a
                yield from start
            while a <= stop:
                yield a
                a += step

        else:
            prefix = seq[: idx + 1]
            suffix = seq[idx + 1 :]
            yield from self._from_sequence(prefix)
            if ... in suffix:
                raise NotImplementedError("contains multiple ranges")
            yield from suffix

    def from_slice(self, slice):
        """
        Create iterator from slice object.
        """

        start = 0 if slice.start is None else slice.start
        step = 1 if slice.step is None else slice.step
        return self.count(start, step, stop=slice.step)

    def count(self, start=0, step=1, stop=None):
        """
        Return values starting from start advancing by the given step.
        """
        out = itertools.count(start, step)
        if stop is not None:
            out = itertools.takewhile(lambda x: x < stop, out)
        return Iter(out)

    def evenly_spaced(self, a: Real, b: Real, n: int) -> Iter:
        """
        Return a sequence of n evenly spaced numbers from a to b.
        """
        return Iter(_evenly_spaced(a, b, n))


def _evenly_spaced(a, b, n):
    a = float(a)
    delta = b - a
    dt = delta / (n - 1)
    for _ in range(n):
        yield a
        a += dt


@_nums
def nums(*args: int) -> Iter[int]:
    """
    Create numeric sequences.

    Examples:
        >>> sk.nums(0, 1, 2, ...)
        sk.iter([0, 1, 2, 3, 4, 5, ...])
    """
    n = len(args)
    if n == 0:
        return Iter(itertools.count(0))
    elif n == 1:
        return Iter(itertools.count(args[0]))
    return Iter(nums.from_sequence(args))


def stop_seq(e):
    if isinstance(e, StopIteration):
        if e.args:
            yield e.args[0]
