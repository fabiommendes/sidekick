import itertools

from ..magics import L, X, Y
from ..core import fn, extract_function, Seq, Func, NOT_GIVEN

__all__ = ['cycle', 'iterate', 'iterate_indexed', 'iterate_past',
           'repeat', 'repeatedly', 'singleton', 'unfold']

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
    return _cycle(seq)


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
    return _repeat(obj, times)


@fn
def repeatedly(func, *args, **kwargs):
    """
    Make infinite calls to a function with the given arguments.

    Examples:
        >>> lst = [1, 2, 3, 4]
        >>> repeatedly(lst.pop) | L[:4]
        [4, 3, 2, 1]
    """
    func = extract_function(func)
    while True:
        yield func(*args, **kwargs)


@fn
def singleton(obj):
    """
    Return single object.

    Examples:
        >>> singleton(42) | L
        [42]
    """
    yield obj


@fn.curry(2)
def unfold(func, seed):
    """
    Invert a fold.

    Similar to iterate, but expects a function of seed -> (seed', x). The second
    value of the tuple is included in the resulting sequence while the first
    is used to seed func in the next iteration. Stops iteration if func returns
    None.

    Examples:
        >>> unfold(lambda x: (x + 1, x), 0) | L[:10]
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

    """
    elem = func(seed)
    while elem is not None:
        seed, x = elem
        yield x
        elem = func(seed)


@fn.curry(2)
def iterate(func, x):
    """
    Repeatedly apply a function func onto an original input.

        iterate(f, x) ==> x, f(x), f(f(x)), ...

    Examples:
        >>> iterate((X * 2), 1) | L[:12]
        [1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048]
    """
    func = extract_function(func)
    yield x
    while True:
        x = func(x)
        yield x


@fn.curry(2)
def iterate_past(func: Func, init: Seq) -> Seq:
    """
    Iterate func and compute next elements by passing the last n elements to
    func.

    Number ``n`` is given by the size of the ``init`` sequence. Elements from
    init are included on the resulting sequence.

    Examples:
        >>> iterate_past((X + Y), [1, 1]) | L[:10]
        [1, 1, 2, 3, 5, 8, 13, 21, 34, 55]
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
        >>> iterate_indexed(lambda i, x: i * x, 1, start=1) | L[:10]
        [1, 1, 2, 6, 24, 120, 720, 5040, 40320, 362880]
    """
    func = extract_function(func)
    yield x
    idx = _count(start) if idx is None else idx
    for i in idx:
        x = func(i, x)
        yield x
