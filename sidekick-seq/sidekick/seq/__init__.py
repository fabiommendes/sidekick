from typing import Sequence

from .iter import iter, generator
from .lib_augmenting import interpose, pad, pad_with, append, insert
from .lib_basic import (
    cons,
    uncons,
    first,
    second,
    nth,
    find,
    last,
    last_n,
    only,
    is_empty,
    length,
    consume,
    peek,
    peek_n,
    first_repeated,
)
from .lib_combining import concat, interleave, zip_aligned, merge_sorted, join, diff
from .lib_creation import cycle, iterate, repeat, repeatedly, singleton, unfold, nums
from .lib_grouping import (
    group_by,
    chunks,
    chunks_by,
    window,
    pairs,
    partition,
    distribute,
    inits,
)
from .lib_reducers import (
    fold,
    reduce,
    scan,
    acc,
    reduce_by,
    fold_by,
    fold_together,
    reduce_together,
    scan_together,
    acc_together,
    product,
    products,
    sum,
    sums,
    all_by,
    any_by,
    top_k,
)
from .lib_selecting import (
    filter,
    remove,
    separate,
    drop,
    drop_at,
    rdrop,
    take,
    rtake,
    take_at,
    strip,
    unique,
    dedupe,
    random_sample,
    indexed,
    converge,
)
from .lib_transforming import map, map_if, zip_map

__version__ = "0.1.0"
__all__ = [
    # Utils
    "as_seq",
    "is_seq",
    # Core
    "iter",
    "generator",
    # Basic
    "cons",
    "uncons",
    "first",
    "second",
    "nth",
    "find",
    "only",
    "last",
    "last_n",
    "is_empty",
    "length",
    "consume",
    "peek",
    "peek_n",
    "first_repeated",
    # Creation
    "cycle",
    "iterate",
    "repeat",
    "repeatedly",
    "singleton",
    "unfold",
    "nums",
    # Selection
    "filter",
    "remove",
    "separate",
    "drop",
    "drop_at",
    "rdrop",
    "take",
    "rtake",
    "take_at",
    "strip",
    "unique",
    "dedupe",
    "converge",
    "random_sample",
    "indexed",
    # Reducers
    "fold",
    "reduce",
    "scan",
    "acc",
    "reduce_by",
    "fold_by",
    "fold_together",
    "reduce_together",
    "scan_together",
    "acc_together",
    "product",
    "products",
    "sum",
    "sums",
    "all_by",
    "any_by",
    "top_k",
    # Grouping
    "group_by",
    "chunks",
    "chunks_by",
    "window",
    "pairs",
    "partition",
    "distribute",
    "inits",
    # Transforming
    "map",
    "map_if",
    "zip_map",
    # Augmenting
    "interpose",
    "pad",
    "pad_with",
    "append",
    "insert",
    # Combining
    "concat",
    "interleave",
    "zip_aligned",
    "merge_sorted",
    "join",
    "diff",
]


#: Utility functions
def is_seq(obj) -> bool:
    """
    Return true if object is a non-string sequence.

    See also:
        as_seq
    """
    return not isinstance(obj, str) and isinstance(obj, Sequence)


def as_seq(obj) -> Sequence:
    """
    Force object to be a sequence.

    Non-sequence arguments and strings are converted into singleton lists.

    See also:
        is_seq
    """
    return obj if is_seq(obj) else [obj]
