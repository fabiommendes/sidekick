import builtins
import itertools
from collections import deque
from typing import Sequence, Callable, Iterable, TYPE_CHECKING

from .iter import iter
from .util import to_callable, to_index_seq, Unpack, Ts, b, a, num, INDEX_DOC, NOT_GIVEN


if TYPE_CHECKING:
    from sidekick import api as sk  # noqa: F401
    from sidekick.api import X, Y  # noqa: F401

_iter = builtins.iter


def cycle(seq: Iterable[a], /, *, n: int = NOT_GIVEN) -> iter[a]:
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
    if n is NOT_GIVEN:
        return iter(itertools.cycle(seq))
    return iter(_cycle_n(n, seq))


# This implementation accepts infinite sequences
def _cycle_n(n, seq):
    buf = []
    add = buf.append
    for x in seq:
        yield x
        add(x)
    yield from itertools.chain.from_iterable(repeat(buf, n - 1))


def repeat(obj: a, /, *, times: int = NOT_GIVEN) -> iter[a]:
    """
    Returns the object for the specified number of times.

    If not specified, returns the object endlessly.

    Examples:
        >>> sk.repeat(42, times=5)
        sk.iter([42, 42, 42, 42, 42])
    """
    if times is NOT_GIVEN:
        return iter(itertools.repeat(obj))
    return iter(itertools.repeat(obj, times))


def repeatedly(func: Callable[..., a], /, *args, **kwargs) -> iter[a]:
    """
    Make infinite calls to a function with the given arguments.

    End sequence if func() raises StopIteration.

    Examples:
        >>> sk.repeatedly(list, (1, 2))
        sk.iter([[1, 2], [1, 2], [1, 2], [1, 2], [1, 2], ...])
    """
    return iter(_repeatedly(func, args, kwargs))


def _repeatedly(func, args, kwargs):
    func = to_callable(func)
    try:
        while True:
            yield func(*args, **kwargs)
    except StopIteration as e:
        yield from stop_seq(e)


def singleton(obj: a) -> iter[a]:
    """
    Return iterator with a single object.

    Args:
        obj:
            Single element of sequence.

    Examples:
        >>> sk.singleton(42)
        sk.iter([42])
    """
    return iter(iter([obj]))


def unfold(func: Callable[[b], tuple[b, a]], seed: b) -> iter[a]:
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
    return iter(_unfold(func, seed))


def _unfold(func, seed):
    try:
        elem = func(seed)
        while elem is not None:
            seed, x = elem
            yield x
            elem = func(seed)
    except StopIteration as e:
        yield from stop_seq(e)


# @overload
# def iterate(
#     func: Callable[[T], T], x: T, /, *, index: int | Iterable[T] | None = None
# ) -> iter[T]:
#     ...


# @overload
# def iterate(
#     func: Callable[[T, T], T], x: T, y: T, /, *, index: int | Iterable[T] | None = None
# ) -> iter[T]:
#     ...


def iterate(
    func: Callable[[Unpack[Ts]], a],
    *args: Unpack[Ts],
    index: int | Iterable[a] = NOT_GIVEN,
) -> iter[a]:
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

    See also:
        :func:`repeatedly` - call function with the same arguments.
    """
    func = to_callable(func)
    index_seq = to_index_seq(index)

    if index_seq is None:
        out = _iterate(func, args)
    else:
        out = _iterate_indexed(func, index_seq, args)
    return iter(out)


def _iterate(func, args):
    try:
        yield from args
        match args:
            case (x,):
                while True:
                    x = func(x)
                    yield x
            case (x, y):
                x, y = args
                while True:
                    x, y = y, func(x, y)
                    yield y
            case _:
                args = deque(args, len(args))
                while True:
                    new = func(*args)
                    args.append(new)
                    yield new
    except StopIteration as e:
        yield from stop_seq(e)


def _iterate_indexed(func, index, args):
    n = len(args)
    try:
        yield from args
        if n == 0:
            yield from map(func, index)
        elif n == 1:
            x = args[0]
            for i in index:
                x = func(i, x)
                yield x
        elif n == 2:
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


class Nums:
    """
    Create numeric sequences.

    Examples:
        >>> sk.nums(0, 1, 2, ...)
        sk.iter([0, 1, 2, 3, 4, 5, ...])
    """

    __slots__ = ()

    def __call__(self, *args: int) -> iter[int]:
        n = len(args)
        if n == 0:
            return iter(itertools.count(0))
        elif n == 1:
            return iter(itertools.count(args[0]))
        return iter(self.from_sequence(args))

    def __getitem__(self, item) -> iter[num]:
        if isinstance(item, tuple):
            return self.from_sequence(item)
        elif isinstance(item, slice):
            return self.from_slice(item)
        else:
            raise TypeError

    def __iter__(self):
        return itertools.count()

    def from_sequence(self, seq: Sequence[num]) -> iter[num]:
        """
        Create iterator from sequence of numbers.
        """
        return iter(_from_sequence(seq))

    def from_slice(self, slice: slice):
        """
        Create iterator from slice object.
        """

        start = 0 if slice.start is None else slice.start
        step = 1 if slice.step is None else slice.step
        return iter(self.count(start, step, stop=slice.step))

    def count(
        self, start: int = 0, step: int = 1, stop: int | None = None
    ) -> iter[int]:
        """
        Return values starting from start advancing by the given step.
        """
        out = itertools.count(start, step)
        if stop is None:
            return iter(out)
        stop_: int = stop
        return iter(itertools.takewhile(lambda x: x < stop_, out))

    def evenly_spaced(self, a: num, b: num, n: int) -> iter[num]:
        """
        Return a sequence of n evenly spaced numbers from a to b.
        """
        return iter(_evenly_spaced(a, b, n))


def _evenly_spaced(a, b, n):
    a = float(a)
    delta = b - a
    dt = delta / (n - 1)
    for _ in range(n):
        yield a
        a += dt


def _from_sequence(seq: Sequence[num]):
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
        yield from _from_sequence(prefix)
        if ... in suffix:
            raise NotImplementedError("contains multiple ranges")
        yield from suffix


nums = Nums()


def stop_seq(e):
    if isinstance(e, StopIteration):
        if e.args:
            yield e.args[0]
