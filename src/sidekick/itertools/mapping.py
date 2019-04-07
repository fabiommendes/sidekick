import itertools

from sidekick import fn, Func, Seq

__all__ = ['indexed_map', 'enumerate']
_map = map
_enumerate = enumerate


@fn.curry(2)
def indexed_map(func: Func, *seqs: Seq, start=0) -> Seq:
    """
    Like map, but pass the index of each element as the first argument to
    func.

    Examples:
        >>> ''.join(indexed_map((X * Y), 'hello', start=1))
        'heelllllllooooo'

    See Also:
        map
    """
    return _map(func, itertools.count(start), *seqs)


# noinspection PyShadowingBuiltins
@fn
def enumerate(seq: Seq, start=0) -> Seq:
    """
    An fn-enabled version of Python's builtin ``enumerate`` function.

    enumerate(seq) ==> (start, seq[0]), (start + 1, seq[1]), ...

    Examples:
        >>> dict(enumerate('hello'))
        {0: 'h', 1: 'e', 2: 'l', 3: 'l', 4: 'o'}
    """
    return _enumerate(seq, start=start)
