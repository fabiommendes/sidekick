from functools import wraps

from .iter import Iter, generator
from .lib_augmenting import interpose, pad, pad_with, append, insert
from .lib_basic import (
    cons,
    uncons,
    first,
    second,
    nth,
    find,
    last,
    only,
    is_empty,
    length,
    consume,
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
    rdrop,
    take,
    rtake,
    unique,
    dedupe,
    converge,
)
from .lib_transforming import map, zip_map

__all__ = [
    # Core
    "Iter",
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
    "is_empty",
    "length",
    "consume",
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
    "rdrop",
    "take",
    "rtake",
    "unique",
    "dedupe",
    "converge",
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
    # Transforming
    "map",
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


def iter(obj):
    """
    Convert iterable to a sidekick Iter() iterator.
    """
    return Iter(obj)


#
# Fluent interface for the Iter class
#
def register_fluent_interface(ns=globals(), blacklist=()):
    from ..functions import fn

    def make_method(idx, func, sig):
        @wraps(func)
        def method(self, *args, **kwargs):
            args = list(args)
            args.insert(idx, self)
            return func(*args, **kwargs)

        method.__signature__ = sig.partial(seq=...)
        return method

    for name in __all__:
        func = ns[name]
        if not isinstance(func, fn) or hasattr(Iter, name) or name in blacklist:
            continue

        sig = func.signature()
        names = sig.argnames()
        try:
            idx = names.index("seq")
        except ValueError:
            continue
        else:
            setattr(Iter, name, make_method(idx, func, sig))

    class Mixin:
        @wraps(map)
        def map(self: Iter, func, index=None):
            return map(func, self, index=index)

        @wraps(filter)
        def filter(self: Iter, func, index=None):
            return filter(func, self, index=index)

        @wraps(zip_map)
        def zip_map(self: Iter, funcs, index=None):
            return zip_map(funcs, self, index=index)

    for k, v in vars(Mixin).items():
        if k.startswith("_"):
            continue
        setattr(Iter, k, v)


register_fluent_interface()
del register_fluent_interface
