import itertools

from ..typing import Index

INDEX_DOC = """index:
            Either a number that starts an infinite enumeration or a sequence
            of indexes that is passed as the first argument to func."""


def to_index_seq(index: Index):
    """
    Convert the index argument of many functions to a proper sequence.
    """
    if index is False or index is None:
        return None
    elif index is True:
        return itertools.count(0)
    elif isinstance(index, int):
        return itertools.count(index)
    else:
        return index


def vargs(args):
    """
    Conform function args to a sequence of sequences.
    """
    n = len(args)
    if n == 1:
        return args[0]
    elif n == 0:
        raise TypeError("no arguments given")
    else:
        return args
