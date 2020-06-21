import itertools

from ..functions import fn, to_callable
from .._iterator import generator, iter as _iter
from ..magics import L, X, Y
from ..typing import Seq, Func

__all__ = [
    "cycle",
    "iterate",
    "iterate_indexed",
    "iterate_past",
    "repeat",
    "repeatedly",
    "singleton",
    "unfold",
]

_enumerate = enumerate
_cycle = itertools.cycle
_repeat = itertools.repeat
_count = itertools.count


@fn
def cycle(seq):
    """
    Return elements from the iterable until it is exhausted.
    Then repeat the sequence indefinitely.

        cycle(seq) ==> seq[0], seq[1], ..., seq[n - 1], seq[0], seq[1], ...

    Examples:
        >>> cycle([1, 2, 3]) | L[:10]
        [1, 2, 3, 1, 2, 3, 1, 2, 3, 1]
    """
    return _iter(_cycle(seq))


@fn.curry(1)
def repeat(obj, *, times=None):
    """
    repeat(obj [,times]) -> create an iterator which returns the object
    for the specified number of times.  If not specified, returns the object
    endlessly.

    Examples:
        >>> repeat(42, times=5) | L
        [42, 42, 42, 42, 42]
    """
    return _iter(_repeat(obj, times))


@fn
@generator
def repeatedly(func, *args, **kwargs):
    """
    Make infinite calls to a function with the given arguments.

    Examples:
        >>> lst = [1, 2, 3, 4]
        >>> repeatedly(lst.pop)[:4]
        sk.iter([4, 3, 2, 1])
    """
    func = to_callable(func)
    while True:
        yield func(*args, **kwargs)


@fn
@generator
def singleton(obj):
    """
    Return iterator with a single object.

    Examples:
        >>> singleton(42)
        sk.iter([42])
    """
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
        >>> unfold(lambda x: (x + 1, x), 0) | L[:10]
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

    """
    try:
        elem = func(seed)
        while elem is not None:
            seed, x = elem
            yield x
            elem = func(seed)
    except StopIteration:
        pass


@fn.curry(2)
@generator
def iterate(func, x):
    """
    Repeatedly apply a function func to input.

        iterate(f, x) ==> x, f(x), f(f(x)), ...

    Examples:
        >>> iterate((X * 2), 1)
        sk.iter([1, 2, 4, 8, 16, 32, 64, ...])
    """
    func = to_callable(func)
    yield x
    while True:
        x = func(x)
        yield x


@fn.curry(2)
@generator
def iterate_past(func: Func, init: Seq) -> Seq:
    """
    Iterate func and compute next element by passing the last n elements to
    func.

    Number ``n`` is given by the size of the ``init`` sequence. Elements from
    init are included on the resulting sequence.

    Examples:
        >>> iterate_past((X + Y), [1, 1]) | L[:10]
        sk.iter([1, 1, 2, 3, 5, 8, 13, ...])
    """

    init = tuple(init)
    n = len(init)

    # Optimize some special cases
    if n == 0:
        while True:
            yield func()

    elif n == 1:
        yield from iterate(func, init[0])

    elif n == 2:
        x, y = init
        yield from init
        while True:
            x, y = y, func(x, y)
            yield y

    elif n == 3:
        x, y, z = init
        yield from init
        while True:
            x, y, z = y, z, func(x, y, z)
            yield z

    else:
        args = init
        yield from init
        while True:
            new = func(*args)
            yield new
            args = args[1:] + (new,)


@fn.curry(2)
@generator
def iterate_indexed(func: Func, x, *, idx: Seq = None, start=0) -> Seq:
    """
    Similar to :func:`iterate`, but also pass the index of element to func.

        for_each(f, x) ==> x, f(0, x), f(1, <previous>), ...

    Args:
        func:
            Iteration function (index, value) -> next_value.
        x:
            Initial value of iteration.
        idx:
            Sequence of indexes. If not given, uses N[start, ...]
        start:
            Starting value for sequence of indexes.

    Examples:
        >>> iterate_indexed(lambda i, x: i * x, 1, start=1)
        sk.iter([1, 1, 2, 6, 24, 120, 720, 5040, 40320, ...])
    """
    func = to_callable(func)
    yield x
    idx = _count(start) if idx is None else idx
    for i in idx:
        x = func(i, x)
        yield x
