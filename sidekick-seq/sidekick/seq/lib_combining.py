import itertools
from typing import Sequence, overload, Iterable, Callable, TYPE_CHECKING

from .iter import iter
from .lib_basic import is_empty
from .util import c, to_callable, vargs, toolz, b, a, Raisable, NOT_GIVEN


if TYPE_CHECKING:
    from sidekick import api as sk  # noqa: F401


class UnalignedZipError(ValueError):
    """
    Raised by zip_aligned when two iterators do not have the same size.
    """

    @classmethod
    def default(cls):
        """
        Create error with default message.
        """
        return cls("sequences are not aligned")


@overload
def concat(seqs: Sequence[Iterable[a]]) -> iter[a]:
    ...


@overload
def concat(seq: Iterable[a], *seqs: Iterable[a]) -> iter[a]:
    ...


def concat(*args):
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
    if len(args) == 1:
        return iter(itertools.chain.from_iterable(args))
    return iter(itertools.chain(*args))


@overload
def interleave(seq: Iterable[a], *, aligned: bool = False) -> iter[a]:
    ...


@overload
def interleave(*seqs: Iterable[a], aligned: bool = False) -> iter[a]:
    ...


def interleave(*args, aligned=False):
    """
    Interleave sequence of sequences.

    Args:
        seqs:
            a sequence of sequences
        aligned:
            If True, stops when the first iterator exhausts. Aligned does not
            work with an infinite sequence of sequences, but all sequences in
            this finite list may be infinite.

    Examples:
        >>> sk.interleave([1, 2, 3], 'abc')
        sk.iter([1, 'a', 2, 'b', 3, 'c'])

        If called with a single argument, it must be a sequence of sequences.

        >>> sk.interleave([[1, 2, 3], 'abc'])
        sk.iter([1, 'a', 2, 'b', 3, 'c'])
    """
    if len(args) == 1:
        args = args[0]
    if aligned:
        return iter(_interleave_aligned(args))
    return iter(toolz.interleave(args))


def _interleave_aligned(seqs):
    nexts = [iter(it).__next__ for it in seqs]
    buffer = []
    fill = buffer.extend

    while True:
        buffer.clear()
        try:
            fill(f() for f in nexts)
            yield from buffer
        except StopIteration:
            break


def zip_aligned(
    *args: Iterable[a], error: Callable[[], Raisable] = UnalignedZipError.default
) -> iter[a]:
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

        >>> sk.zip_aligned((1, 2, 3), (4, 5, 6, 7)).last()
        Traceback (most recent call last):
        ...
        UnalignedZipError: sequences are not aligned
    """
    return iter(_zip_aligned(args, error))


def _zip_aligned(args, error):
    args = tuple(map(iter, args))
    yield from zip(*args)
    if not all(map(is_empty, args)):
        raise error()


def diff(
    *seqs: Iterable[a], key: Callable[[a], b] = NOT_GIVEN, default=NOT_GIVEN
) -> iter[tuple[a, a]]:
    """
    Return those items that differ in a pairwise comparison between sequences.

    Examples:
        >>> sk.diff([1, 2, 3, 4], [1, 2, 4, 8])
        sk.iter([(3, 4), (4, 8)])
    """
    kwargs = {}
    if key is not NOT_GIVEN:
        kwargs["key"] = to_callable(key)
    if default is not NOT_GIVEN:
        kwargs["default"] = default
    return iter(toolz.diff(*vargs(seqs), **kwargs))


def join(
    leftkey: Callable[[a], c],
    leftseq: Iterable[a],
    rightkey: Callable[[b], c],
    rightseq: Iterable[b],
    **kwargs,
) -> iter[b]:
    """
    Join two sequences on common attributes.
    """

    leftkey = to_callable(leftkey)
    rightkey = to_callable(rightkey)
    return iter(toolz.join(leftkey, leftseq, rightkey, rightseq, **kwargs))


@overload
def merge_sorted(
    seqs: Sequence[Iterable[a]], /, *, key: Callable[[a], a] = NOT_GIVEN
) -> iter[a]:
    ...


@overload
def merge_sorted(
    seq: Iterable[a], /, *seqs: Iterable[a], key: Callable[[a], a] = NOT_GIVEN
) -> iter[a]:
    ...


def merge_sorted(*seqs, key=NOT_GIVEN):
    """
    Merge and sort a collection of sorted collections.

    Examples:
        >>> sk.merge_sorted(sk.nums(1, 3, ..., 9), sk.nums(0, 2, ..., 10))
        sk.iter([0, 1, 2, 3, 4, 5, ...])
    """
    seqs = seqs[0] if len(seqs) == 1 else seqs
    if key is NOT_GIVEN:
        key_ = None
    else:
        key_ = to_callable(key)
    return iter(toolz.merge_sorted(*seqs, key=key_))
