import itertools
from numbers import Real

from ..core import fn, extract_function, Seq, Func

__all__ = ['cycle', 'evenly_spaced', 'frange', 'numbers',
           'iterate', 'iterate_indexed', 'iterate_past',
           'repeat', 'repeatedly', 'singleton']

_enumerate = enumerate


@fn
def cycle(seq):
    """
    Return elements from the iterable until it is exhausted.
    Then repeat the sequence indefinitely.

    For a sequence of size n:

    cycle(seq) ==> seq[0], seq[1], ..., seq[n - 1], seq[0], seq[1], ...
    """
    return itertools.cycle(seq)


@fn.annotate(3)
def evenly_spaced(a: Real, b: Real, n: int) -> Seq:
    """
    Return a sequence of n evenly spaced numbers from a to b.
    """
    delta = b - a
    dt = delta / (n - 1)
    for _ in range(n):
        yield a
        a += dt


@fn.annotate(2)
def frange(*args):
    """
    Similar to range, but accepts float values.

    It does not accept the single argument invocation (use range for that).

    frange(start, stop) ==> start, start + 1, ... (until smaller than stop)
    frange(start, stop, delta) ==> start, start + delta, ...
    """
    arity = len(args)
    if arity == 2:
        start, stop = args
        delta = 1
    elif arity == 3:
        start, stop, delta = args
    else:
        raise TypeError('must be called with one or two arguments')

    x = start
    while x < stop:
        yield x
        x += delta


@fn.annotate(2)
def iterate(func, x):
    """
    Repeatedly apply a function func onto an original input.

        iterate(f, x) ==> x, f(x), f(f(x)), ...
    """
    func = extract_function(func)
    yield x
    while True:
        x = func(x)
        yield x


@fn.annotate(2)
def iterate_indexed(func: Func, x, *, start: int = 0) -> Seq:
    """
    Similar to :func:`iterate`, but also pass the index of element to func.

        iterate(f, x) ==> x, f(0, x), f(1, f(0, x)), ...

    You can also specify the starting index to be different than zero.
    """
    func = extract_function(func)
    yield x
    while True:
        x = func(start, x)
        yield x
        start += 1


@fn.curry(3)
def iterate_past(n: int, func: Func, init: Seq, *, start: int = 0) -> Seq:
    """
    Iterate func and compute next elements by passing the past n elements to
    func.

    Initial sequence must have exactly n elements.
    """

    init = tuple(init)
    if len(init) != n:
        raise ValueError(f'initial sequence needs at least {n} values')
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


@fn
def numbers(start=0, step=1):
    """
    Return sequence of numbers.

    count(start, step) ==> start, start + step, start + 2 * step, ...
    """
    return itertools.count(start, step)


@fn.annotate(1)
def repeat(obj, *, times=None):
    """
    repeat(obj [,times]) -> create an iterator which returns the object
    for the specified number of times.  If not specified, returns the object
    endlessly.
    """
    return itertools.repeat(obj, times)


@fn
def repeatedly(func, *args, **kwargs):
    """
    Make n or infinite calls to a function.

    Can be called with function or a tuple of (function, repetitions) as the
    first argument. Additional arguments are passed to the function at each
    call.
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
    """
    yield obj
