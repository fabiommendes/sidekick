import itertools

from .iter import generator, iter as _iter
from ..functions import fn, to_callable
from ..typing import Seq, Func, TYPE_CHECKING

if TYPE_CHECKING:
    from .. import api as sk
    from ..api import X, Y

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
        >>> sk.cycle([1, 2, 3])
        sk.iter([1, 2, 3, 1, 2, 3, ...])
    """
    return _iter(_cycle(seq))


@fn.curry(1)
def repeat(obj, *, times=None):
    """
    repeat(obj [,times]) -> create an iterator which returns the object
    for the specified number of times.  If not specified, returns the object
    endlessly.

    Examples:
        >>> sk.repeat(42, times=5)
        sk.iter([42, 42, 42, 42, 42])
    """
    return _iter(_repeat(obj, times))


@fn
@generator
def repeatedly(func, *args, **kwargs):
    """
    Make infinite calls to a function with the given arguments.

    Stop iteration if func() raises StopIteration.

    Examples:
        >>> sk.repeatedly(list, (1, 2))
        sk.iter([[1, 2], [1, 2], [1, 2], [1, 2], [1, 2], ...])
    """
    func = to_callable(func)
    try:
        while True:
            yield func(*args, **kwargs)
    except StopIteration:
        pass


@fn
@generator
def singleton(obj):
    """
    Return iterator with a single object.

    Examples:
        >>> sk.singleton(42)
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
        >>> sk.unfold(lambda x: (x + 1, x), 0)
        sk.iter([0, 1, 2, 3, 4, 5, ...])

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
def iterate(func, x, *args):
    """
    Repeatedly apply a function func to input.

    If more than one argument to func is passed, it iterate over the past n
    values. It requires at least one argument, if you need to iterate a zero
    argument function, call :func:`repeatedly`

    Iteration stops if if func() raise StopIteration.

        iterate(f, x) ==> x, f(x), f(f(x)), ...

    Examples:
        Simple usage, with a single argument. Produces powers of two.

        >>> sk.iterate((X * 2), 1)
        sk.iter([1, 2, 4, 8, 16, 32, ...])

        Now we call with two arguments to func to produce Fibonacci numbers

        >>> sk.iterate((X + Y), 1, 1)
        sk.iter([1, 1, 2, 3, 5, 8, ...])

    See Also:
        :func:`repeatedly`
    """
    func = to_callable(func)

    if not args:
        try:
            yield x
            while True:
                x = func(x)
                yield x
        except StopIteration:
            return

    # Optimize some special cases

    init = (x, *args)
    n = len(init)
    yield from init

    try:
        if n == 2:
            x, y = init
            while True:
                x, y = y, func(x, y)
                yield y

        elif n == 3:
            # noinspection PyTupleAssignmentBalance
            x, y, z = init
            while True:
                x, y, z = y, z, func(x, y, z)
                yield z

        else:
            args = init
            while True:
                new = func(*args)
                _, *args = args
                args = (*args, new)
                yield new
    except StopIteration:
        return


@fn.curry(2)
@generator
def iterate_indexed(func: Func, x, *args, idx: Seq = None, start=0) -> Seq:
    """
    Similar to :func:`iterate`, but also pass the index of element to func.

        iterate_indexed(f, x) ==> x, f(0, x), f(1, <previous>), ...

    Args:
        func:
            Iteration function (index, value) -> next_value.
        x:
            Initial value of iteration.
        idx:
            Sequence of indexes. If not given, uses start, start + 1, ...
        start:
            Starting value for sequence of indexes.

    Examples:
        >>> sk.iterate_indexed(lambda i, x: i * x, 1, start=1)
        sk.iter([1, 1, 2, 6, 24, 120, ...])
    """
    func = to_callable(func)
    yield x
    idx = _count(start) if idx is None else idx

    if not args:
        for i in idx:
            x = func(i, x)
            yield x
    else:
        yield from args
        args = (x, *args)

        for i in idx:
            new = func(i, *args)
            yield new
            args = args[1:] + (new,)
