import itertools

from .iter import Iter
from .util import to_index_seq
from ..functions import fn, to_callable
from ..typing import Func, Seq, Index, TYPE_CHECKING, Pred

if TYPE_CHECKING:
    from ..api import sk, X, Y, op  # noqa: F401

_map = map


@fn.curry(2)
def map(func: Func, *seqs: Seq, index: Index = None, product: bool = None) -> Iter:
    """
    Evaluate function at elements of sequences.

        sk.map(func, *seqs) ==> f(X[0], Y[0], ...), f(X[1], Y[1], ...), ...

    in which X, Y, Z, ... are the sequences in seqs. Stops when the shortest iterable
    is exhausted.

    Args:
        func:
            Function to be applied in sequences.
        seqs:
            Input sequences.
        index:
            If true, pass the index as the first argument. If indexed is an
            integer, it is interpreted as the starting index for counting.
        product:
            If True, apply function to all combinations of tuples created by
            the input sequences. In this case, it interprets tuples of integers
            as the starting indexes of the iterator index in each dimension.

    Examples:
        A simple map: apply function to list or sequence

        >>> sk.map(str.upper, ['Hello', 'World!'])
        sk.iter(['HELLO', 'WORLD'])

        Map also accepts functions of several parameters, which are extracted
        in parallel from different sequences.

        >>> sk.map((X + Y), [1, 2, 3], [4, 5, 6])
        sk.iter([5, 7, 9])

        If indexed mode is enabled, the index is passed as the first argument
        to function.

        >>> sk.map((X * Y), [1, 2, 3], index=True)
        sk.iter([0, 2, 6])

        This is equivalent to anyone of those forms

        >>> sk.map((X * Y), [1, 2, 3], index=sk.nums(0, ...))
        sk.iter([0, 2, 6])
        >>> sk.map((X * Y), sk.nums(0, ...), [1, 2, 3])
        sk.iter([0, 2, 6])

        Indexes, however, behave differently when map is called in the product
        mode. This mode expands the mapping to all permutations of elements of
        each sequence argument.

        >>> sk.map((X * Y), [1, 2], [3, 4, 5], product=True)
        sk.iter([3, 4, 5, 6, 8, ...])
        >>> sk.map(lambda i, x, y: (i, x * y), [1, 2], [3, 4, 5], product=True, index=(0, 0))
        sk.iter([(0, 3), (1, 4), (2, 5), (0, 6), (1, 8), ...])
    """
    if not seqs:
        raise TypeError("requires at least one input sequence")

    func = to_callable(func)

    if product:
        if index is None:
            return Iter(_map(lambda args: func(*args), itertools.product(*seqs)))
        elif isinstance(index, tuple):
            if not len(seqs) == len(index):
                raise ValueError("indexes and sequences must align")
            seqs = (enumerate(seq, i) for i, seq in zip(index, seqs))
            return Iter(_map(func, itertools.product(*seqs)))
        else:
            index = to_index_seq(index)
            map_fn = lambda i, args: func(i, *args)
            return Iter(_map(map_fn, index, itertools.product(*seqs)))
    elif index is None:
        return Iter(_map(func, *seqs))
    else:
        index = to_index_seq(index)
        return Iter(_map(func, index, *seqs))


@fn.curry(3)
def map_if(pred: Pred, func: Func, *seqs: Seq, index: Index = None) -> Iter:
    """
    Applies func in the elements in which pred(elem) is True.

    If more than one sequence is given, non-transformed elements are obtained
    from the first sequence.

    Args:
        pred:
            Predicate function that selects which elements will be transformed
            with func. Predicate receive the same arguments as func.
        func:
            Function to be applied in sequences.
        seqs:
            Input sequences.
        index:
            If true, pass the index as the first argument. If indexed is an
            integer, it is interpreted as the starting index for counting.

    Examples:
        >>> sk.map_if(str.isdigit, int, ['1', '42', '1kg'])
        sk.iter([1, 42, '1kg'])
    """
    if not seqs:
        raise TypeError("requires at least one input sequence")

    index = to_index_seq(index)
    if index is not None:
        seqs = (index, *seqs)

    if len(seqs) == 1:
        map_func = lambda x: func(x) if pred(x) else x
    elif index:
        map_func = lambda *args: func(*args) if pred(*args) else args[1]
    else:
        map_func = lambda *args: func(*args) if pred(*args) else args[0]

    return Iter(_map(map_func, *seqs))


@fn.curry(2)
def zip_map(funcs: Seq[Func], *seqs: Seq, index: Index = None) -> Iter:
    """
    Apply sequence of functions to sequences of arguments.

    Generalizes map to receive a stream of functions instead of a single one.

    Args:
        funcs:
            A sequence of functions
        seqs:
            Values that will be passed as arguments to functions.
        index:
            If true, pass the index as the first argument. If indexed is an
            integer, it is interpreted as the starting index for counting.

    Examples:
        >>> funcs = op.add, op.sub, op.mul, op.div
        >>> sk.zip_map(funcs, [1, 2, 3, 4], index=True)
        sk.iter([1, -1, 6, 0.75])
    """
    funcs = iter(funcs)
    _to_callable = to_callable
    _next = next

    def func(*args):
        f = _to_callable(_next(funcs))
        return f(*args)

    return map(func, *seqs, index=index)
