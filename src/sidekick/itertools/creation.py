import itertools

from ..core import fn, extract_function, Seq, Func

__all__ = ['cons', 'cycle', 'iterate', 'iterate_indexed', 'iterate_past',
           'repeat', 'repeatedly', 'singleton', 'uncons']

_enumerate = enumerate
NOT_GIVEN = object()


@fn
def cons(x, seq: Seq) -> Seq:
    """
    Add x to beginning of sequence.

    Examples:
        >>> cons(0, N[1, ..., 5]) | L
        [0, 1, 2, 3, 4, 5]
    """
    yield x
    yield from seq


@fn
def uncons(seq: Seq, default=NOT_GIVEN) -> (object, Seq):
    """
    De-construct sequence. Return a pair of (first, rest) of sequence.

    Examples:
        >>> n, seq = uncons(N[1, ..., 5])
        >>> list(seq)
        [2, 3, 4, 5]
    """
    seq = iter(seq)
    try:
        return next(seq), seq
    except StopIteration:
        if default is NOT_GIVEN:
            raise ValueError('Cannot deconstruct empty sequence.')
        return default, iter(())


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
    return itertools.cycle(seq)


@fn.curry(2)
def iterate(func, x):
    """
    Repeatedly apply a function func onto an original input.

        iterate(f, x) ==> x, f(x), f(f(x)), ...

    Examples:
        >>> iterate(lambda x: 2 * x, 1) | L[:12]
        [1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048]
    """
    func = extract_function(func)
    yield x
    while True:
        x = func(x)
        yield x


@fn.curry(2)
def iterate_indexed(func: Func, x, *, start: int = 0) -> Seq:
    """
    Similar to :func:`iterate`, but also pass the index of element to func.

        iterate(f, x) ==> x, f(0, x), f(1, f(0, x)), ...

    You can also specify the starting index to be different than zero.

    Examples:
        >>> iterate_indexed(lambda i, x: i * x, 1, start=1) | L[:10]
        [1, 1, 2, 6, 24, 120, 720, 5040, 40320, 362880]
    """
    func = extract_function(func)
    idx = start
    yield x
    while True:
        x = func(idx, x)
        yield x
        idx += 1


@fn.curry(2)
def iterate_past(func: Func, init: Seq) -> Seq:
    """
    Iterate func and compute next elements by passing the last n elements to
    func.

    Number ``n`` is given by the size of the ``init`` sequence. Elements from
    init are included on the resulting sequence.

    Examples:
        >>> iterate_past(X + Y, [1, 1]) | L[:10]
        [1, 1, 2, 3, 5, 8, 13, 21, 34, 55]
    """

    init = tuple(init)
    n = len(init)
    yield from init

    # Special cases
    if n == 0:
        while True:
            yield func()

    elif n == 1:
        yield from iterate(func, init[-1])

    elif n == 2:
        x, y = init
        while True:
            x, y = y, func(x, y)
            yield y

    elif n == 3:
        x, y, z = init
        while True:
            x, y, z = y, z, func(x, y, z)
            yield z

    else:
        args = init
        while True:
            args = args[1:] + (func(*args),)
            yield args[-1]


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
    return itertools.repeat(obj, times)


@fn
def repeatedly(func, *args, **kwargs):
    """
    Make n or infinite calls to a function.

    Can be called with function or a tuple of (function, repetitions) as the
    first argument. Additional arguments are passed to the function at each
    call.

    Examples:
        >>> lst = [1, 2, 3, 4]
        >>> repeatedly(lst.pop) | L[:4]
        [4, 3, 2, 1]
    """
    func, n = func if isinstance(func, tuple) else (func, None)
    func = extract_function(func)
    seq = itertools.count() if n is None else range(n)

    if not (args or kwargs):
        return (func() for _ in seq)
    else:
        return (func(*args, **kwargs) for _ in seq)


@fn
def singleton(obj):
    """
    Return single object.

    Examples:
        >>> singleton(42) | L
        [42]
    """
    yield obj
