import itertools

from .iter import Iter, generator
from .lib_basic import is_empty
from .util import vargs
from .. import _toolz as toolz
from ..functions import fn
from ..typing import Seq, Union, Raisable, Callable, Func, TYPE_CHECKING, NOT_GIVEN

if TYPE_CHECKING:
    from .. import api as sk, to_callable  # noqa: F401


class UnalignedZipError(Exception):
    """
    Raised by zip_aligned when two iterators do not have the same size.
    """

    @classmethod
    def default(cls):
        """
        Create error with default message.
        """
        return cls("sequences are not aligned")


@fn
def concat(seqs: Union[Seq, Seq[Seq]], *extra) -> Iter:
    """
    Concatenates all iterators in sequence of iterators.

    If called with a single argument, it must be a a sequence of sequences.
    Otherwise, each argument is treated like a input sequence.

    Examples:
        >>> sk.concat([1, 2, 3], [4, 5, 6])
        sk.iter([1, 2, 3, 4, 5, 6])

        It can concatenate (possibly infinite iterators)
        >>> sk.concat(map(range, sk.nums(1, ...)))
        sk.iter([0, 0, 1, 0, 1, 2, ...])
    """
    if extra:
        return Iter(itertools.chain(seqs, *extra))
    return Iter(itertools.chain.from_iterable(seqs))


@fn
def interleave(seqs: Union[Seq, Seq[Seq]], *extra):
    """
    Interleave sequence of sequences.

    Examples:
        >>> sk.interleave([1, 2, 3], 'abc')
        sk.iter([1, 'a', 2, 'b', 3, 'c'])

        If called with a single argument, it must be a sequence of sequences.

        >>> sk.interleave([[1, 2, 3], 'abc'])
        sk.iter([1, 'a', 2, 'b', 3, 'c'])
    """
    if extra:
        seqs = (seqs, *extra)
    return Iter(toolz.interleave(seqs))


@generator
def zip_aligned(
    *args: Seq, error: Callable[[], Raisable] = UnalignedZipError.default
) -> Iter:
    """
    Zip and raises an error if sizes do not match.

    Similar to the zip built-in, but raises an UnalignedZipError if one sequence
    terminates before the others.

    Args:
        args:
            Input sequences, passed as positional arguments.
        error:
            If given, changes the error raised when sequences are not aligned.

    Examples:
        If sizes match, it is just like zip.

        >>> sk.zip_aligned((1, 2, 3), (4, 5, 6))
        sk.iter([(1, 4), (2, 5), (3, 6)])

        But gives an error otherwise.

        >>> sk.zip_aligned((1, 2, 3), (4, 5, 6, 7))
        Traceback (most recent call last):
        ...
        UnalignedZipError: sequences are not aligned
    """
    args = tuple(map(iter, args))
    yield from zip(*args)
    if not all(map(is_empty, args)):
        raise error()


@fn
def diff(*seqs: Seq, key: Func = None, default=NOT_GIVEN) -> Iter:
    """
    Return those items that differ in a pairwise comparison between sequences.

    Examples:
        >>> sk.diff([1, 2, 3, 4], [1, 2, 4, 8])
        sk.iter([(3, 4), (4, 8)])
    """
    kwargs = {}
    if key is not None:
        kwargs["key"] = to_callable(key)
    if default is not NOT_GIVEN:
        kwargs["default"] = default
    return Iter(toolz.diff(*vargs(seqs), **kwargs))


@fn.curry(4)
def join(leftkey: Func, leftseq: Seq, rightkey: Func, rightseq: Seq, **kwargs) -> Iter:
    """
    Join two sequences on common attributes.
    """

    leftkey = to_callable(leftkey)
    rightkey = to_callable(rightkey)
    return Iter(toolz.join(leftkey, leftseq, rightkey, rightseq, **kwargs))


@fn
def merge_sorted(*seqs, key=None) -> Iter:
    """
    Merge and sort a collection of sorted collections.

    Examples:
        >>> sk.merge_sorted(sk.nums(1, 3, ..., 9), sk.nums(0, 2, ..., 10))
        sk.iter([0, 1, 2, 3, 4, 5, ...])
    """
    seqs = seqs[0] if len(seqs) == 1 else seqs
    key = key and to_callable(key)
    return Iter(toolz.merge_sorted(*seqs, key=key))
