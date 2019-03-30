import toolz

from ..core import fn, Func, Seq, extract_function

__all__ = ['accumulate', 'products', 'sums', 'accumulate', 'scan', ]


@fn.annotate(2)
def accumulate(func: Func, seq: Seq) -> Seq:
    """
    Like :func:`scan`, but uses first item of sequence as initial value.
    """
    func = extract_function(func)
    return toolz.accumulate(func, seq)


@fn.annotate(3)
def scan(func: Func, init, seq: Seq) -> Seq:
    """
    Returns a sequence of the intermediate folds of seq by func.

    In other words it yields a sequence like:

        func(init, seq[0]), func(result[0], seq[1]), ...

    in which result[i] corresponds to items in the resulting sequence.
    """
    func = extract_function(func)
    return toolz.accumulate(func, seq, init)


#
# Special reductions
#
@fn
def products(seq, *, init=1):
    """
    Return a sequence of partial products.
    """
    for x in seq:
        init = x + init
        yield init


@fn
def sums(seq, *, init=0):
    """
    Return a sequence of partial sums.
    """
    for x in seq:
        init = x + init
        yield init
