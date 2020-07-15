import itertools
import typing
from typing import Iterable

from .. import _toolz as toolz
from ..functions import fn
from ..typing import Seq


@fn.curry(2)
def pluck(idx, seqs: Iterable[Seq], **kwargs) -> Iter:
    """
    Maps :func:`get` over each sequence in seqs.
    """
    return toolz.pluck(idx, seqs, **kwargs)


@fn
def tee(seq: Seq, n: int = 2) -> typing.Tuple:
    """
    Return n copies of iterator that can be iterated independently.
    """
    return itertools.tee(seq, n)


def vargs(args):
    return args[0] if len(args) == 1 else args
