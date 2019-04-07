import itertools
import typing
from typing import Iterable

import toolz
from sidekick import extract_function, fn, Seq

from ..core import fn, Seq, Function

__all__ = [
    'append', 'cons', 'concat', 'continue_with', 'insert', 'interleave', 'interpose', 'mapcat',
    'diff', 'join', 'merge_sorted', 'pluck']


@fn.annotate(2)
def append(elem, seq):
    """
    Return a new sequence with element el appended to the end.
    """
    yield from seq
    yield elem


@fn
def concat(seqs: Iterable[Seq]) -> Seq:
    """
    Concatenates all iterators in sequence of iterators.
    """
    return toolz.concat(seqs)


@fn.curry(2)
def fill_with(func: Function, seq: Seq):
    """
    After exhausting seq, continue computing value from func(i), in which i
    is the index of the item in the final iterator.

    Examples:
        >>> fill_with((X // 2), [1, 2, 3]) | L[:5]
        [1, 2, 3, 1, 2]
    """
    func = extract_function(func)
    n = 0
    for n, x in enumerate(seq):
        yield x
    yield from (func(n) for n in count(n + 1))


@fn.curry(2)
def fill(value, seq: Seq) -> Seq:
    """
    Fill resulting sequence with value after the first sequence terminates.

    Examples:
        >>> fill(None, [1, 2, 3]) | L[:5]
        [1, 2, 3, None, None]
    """
    yield from seq
    yield from repeat(value)


@fn.annotate(3)
def insert(idx: int, value, seq: Seq) -> Seq:
    """
    Return sequence that inserts value at the given index.
    """
    seq = iter(seq)
    yield from itertools.islice(seq, idx)
    yield value
    yield from seq


@fn
def interleave(seqs):
    """
    Interleave sequence of sequences.

    >>> from sidekick import L
    >>> interleave([[1, 2, 3], 'abc']) | L
    [1, 'a', 2, 'b', 3, 'c']
    """
    return toolz.interleave(seqs)


@fn.annotate(2)
def interpose(elem, seq: Seq) -> Seq:
    """
    Introduce element between each pair of elements in seq.
    """
    return toolz.interpose(elem, seq)


@fn.annotate(2)
def mapcat(func: Function, seqs: Iterable[Seq]) -> Seq:
    """
    Apply func to each sequence in seqs, concatenating results.
    """
    return toolz.mapcat(extract_function(func), seqs)


#
# Multiple sequences
#
@fn
def diff(seqs, *, key=None, **kwargs):
    """
    Return those items that differ in a pairwise comparison between sequences.
    """
    if key is not None:
        kwargs['key'] = extract_function(key)
    return toolz.diff(*seqs, **kwargs)


@fn.annotate(4)
def join(leftkey: Function, leftseq: Seq, rightkey: Function, rightseq: Seq, **kwargs) -> Seq:
    """
    Join two sequences on common attributes.
    """
    leftkey = extract_function(leftkey)
    rightkey = extract_function(rightkey)
    return toolz.join(leftkey, leftseq, rightkey, rightseq, **kwargs)


@fn.annotate(1)
def merge_sorted(seqs, *, key=None):
    """
    Merge and sort a collection of sorted collections.
    """
    key = key and extract_function(key)
    return toolz.merge_sorted(*seqs, key=key)


@fn.annotate(2)
def pluck(idx, seqs: Iterable[Seq], **kwargs) -> Seq:
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


