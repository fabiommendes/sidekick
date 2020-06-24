from itertools import count

from .iter import iter as sk_iter
from ..functions import fn, to_callable
from ..typing import Func, Seq, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from ..api import X, Y, op

_map = map


@fn.curry(2)
def map(func: Func, *seqs: Seq, indexed: Union[int, bool] = False) -> Seq:
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
        indexed:
            If true, pass the index as the first argument. If indexed is an
            integer, it is interpreted as the starting index for counting.

    Examples:
        >>> sk.map((X + Y), [1, 2, 3], [4, 5, 6])
        sk.iter([5, 7, 9])
        >>> sk.map((X * Y), [1, 2, 3], indexed=True)
        sk.iter([0, 2, 6])
    """

    if indexed is True:
        indexed = 0
    if indexed is not False:
        seqs = (count(indexed), *seqs)

    func = to_callable(func)
    return sk_iter(_map(func, *seqs))


@fn.curry(2)
def zip_map(funcs: Seq[Func], *seqs: Seq, indexed: Union[int, bool] = False) -> Seq:
    """
    Apply sequence of functions to sequences of arguments.

    Generalizes map to receive a stream of functions instead of a single one.

    Args:
        funcs:
            A sequence of functions
        seqs:
            Values that will be passed as arguments to functions.
        indexed:
            If true, pass the index as the first argument. If indexed is an
            integer, it is interpreted as the starting index for counting.

    Examples:
        >>> funcs = op.add, op.sub, op.mul, op.div
        >>> sk.zip_map(funcs, [1, 2, 3, 4], indexed=True)
        sk.iter([1, -1, 6, 0.75])
    """
    funcs = iter(funcs)

    def func(*args):
        f = to_callable(next(funcs))
        return f(*args)

    return map(func, *seqs, indexed=indexed)
