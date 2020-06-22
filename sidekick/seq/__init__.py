from .iter import iter, generator
from .lib_basic import cons, uncons, first, second, nth, last, only, is_empty, length
from .lib_creation import (
    cycle,
    iterate,
    iterate_indexed,
    repeat,
    repeatedly,
    singleton,
    unfold,
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
)

__all__ = [
    # Core
    "iter",
    "generator",
    # Basic
    "cons",
    "uncons",
    "first",
    "second",
    "nth",
    "only",
    "last",
    "is_empty",
    "length",
    # Creation
    "cycle",
    "iterate",
    "iterate_indexed",
    "repeat",
    "repeatedly",
    "singleton",
    "unfold",
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
]
