import itertools
from collections import deque

from .iter import Iter, generator
from .lib_basic import uncons
from .. import _toolz as toolz
from ..functions import fn
from ..typing import Seq, TYPE_CHECKING, NOT_GIVEN, Func, T

if TYPE_CHECKING:
    from .. import api as sk  # noqa: F401


@fn.curry(2)
def interpose(elem, seq: Seq) -> Iter:
    """
    Introduce element between each pair of elements in seq.

    Examples:
        >>> sk.interpose("a", [1, 2, 3])
        sk.iter([1, 'a', 2, 'a', 3])
    """
    return Iter(toolz.interpose(elem, seq))


@fn.curry(2)
def pad(value, seq: Seq, size: int = None, step: int = None) -> Iter:
    """
    Fill resulting sequence with value after the first sequence terminates.

    Args:
        value:
            Value used to pad sequence.
        seq:
            Input sequence.
        size:
            Optional minimum size of sequence.
        step:
            If given, pad at a multiple of step.

    Examples:
        >>> sk.pad(0, [1, 2, 3])
        sk.iter([1, 2, 3, 0, 0, 0, ...])

        >>> sk.pad(0, [1, 2, 3], step=2)
        sk.iter([1, 2, 3, 0])

        >>> sk.pad(0, [1, 2, 3], size=5)
        sk.iter([1, 2, 3, 0, 0])
    """
    if step is None:
        out = itertools.chain(seq, itertools.repeat(value))
    else:
        out = _pad_multiple(value, seq, step)
    if size is not None:
        out = itertools.islice(out, size)
    return Iter(out)


def _pad_multiple(value, seq, n):
    i = 0
    for i, x in enumerate(seq, 1):
        yield x
    i %= n
    if i:
        yield from itertools.repeat(value, i)


@fn.curry(2)
def pad_with(func: Func, seq: Seq, nargs=1, default=NOT_GIVEN) -> Iter:
    """
    Pad sequence iterating the last item with func.

    If func is None, fill in with the last value or default, if sequence
    is empty.

    Args:
        func:
            A function to iterate the tail of sequence.
        seq:
            Input sequence.
        nargs:
            The number of elements to pass to func to construct the next
            argument.
        default:
            Fill sequence with this value if it is not large enough.

    Examples:
        >>> sk.pad_with(None, [1, 2, 3])
        sk.iter([1, 2, 3, 3, 3, 3, ...])

        >>> sk.pad_with(op.add(2), [1, 2, 3])
        sk.iter([1, 2, 3, 5, 7, 9, ...])

        Fibonacci numbers

        >>> sk.pad_with(op.add, [1, 1], nargs=2)
        sk.iter([1, 1, 2, 3, 5, 8, ...])

    """
    if func is None:
        out = _pad_last(seq, default)
    elif nargs == 1:
        out = _pad_iterate(func, seq, default)
    else:
        if default is not NOT_GIVEN:
            seq = itertools.chain(itertools.repeat(default, nargs), seq)
            out = itertools.islice(_pad_iterate_n(nargs, func, seq), nargs)
        else:
            out = _pad_iterate_n(nargs, func, seq)
    return Iter(out)


def _pad_last(seq, default):
    x, rest = uncons(seq, default=default)
    yield x
    for x in rest:
        yield x
    yield from itertools.repeat(x)


def _pad_iterate(func, seq, default):
    x, rest = uncons(seq, default=default)
    yield x
    for x in rest:
        yield x
    while True:
        x = func(x)
        yield x


def _pad_iterate_n(n, func, seq):
    args = deque((), n)
    for x in seq:
        yield x
        args.append(x)
    if len(args) != n:
        raise ValueError(f"sequence must have at least {n} items")
    while True:
        x = func(*args)
        yield x
        args.append(x)


@fn.curry(2)
def append(elem: T, seq: Seq[T]) -> Iter[T]:
    """
    Return a new sequence with element appended to the end.

    Examples:
        >>> sk.append(4, [1, 2, 3])
        sk.iter([1, 2, 3, 4])
    """
    return Iter(itertools.chain(seq, [elem]))


@fn.curry(3)
@generator
def insert(idx: int, value: T, seq: Seq[T]) -> Iter[T]:
    """
    Return sequence that inserts value at the given index.

    Examples:
        >>> sk.insert(2, 2.5, [1, 2, 3])
        sk.iter([1, 2, 2.5, 3])

    """
    seq = iter(seq)
    yield from itertools.islice(seq, idx)
    yield value
    yield from seq
