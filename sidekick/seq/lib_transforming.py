from .iter import iter as sk_iter
from .util import to_index_seq
from ..functions import fn, to_callable
from ..typing import Func, Seq, Index, TYPE_CHECKING

if TYPE_CHECKING:
    from ..api import X, Y, op

_map = map


@fn.curry(2)
def map(func: Func, *seqs: Seq, index: Index = None) -> Seq:
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

    Examples:
        >>> sk.map((X + Y), [1, 2, 3], [4, 5, 6])
        sk.iter([5, 7, 9])
        >>> sk.map((X * Y), [1, 2, 3], index=True)
        sk.iter([0, 2, 6])
    """

    index = to_index_seq(index)
    func = to_callable(func)
    if index is None:
        return sk_iter(_map(func, *seqs))
    else:
        return sk_iter(_map(func, index, *seqs))


@fn.curry(2)
def zip_map(funcs: Seq[Func], *seqs: Seq, index: Index = None) -> Seq:
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
