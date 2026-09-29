import itertools
from typing import (
    TYPE_CHECKING,
    Any,
    Iterable,
    ParamSpec,
    Type,
    TypeAlias,
    TypeVar,
    Protocol,
    Hashable,
)
from typing_extensions import Unpack, TypeVarTuple

Unpack = Unpack

if TYPE_CHECKING:
    import toolz  # always type checks as toolz
else:
    try:
        import cytoolz as toolz
    except ImportError:
        import toolz  # noqa

toolz = toolz


#
# Types
#
a = TypeVar("a")
b = TypeVar("b")
c = TypeVar("c")
Ts = TypeVarTuple("Ts")
T_contra = TypeVar("T_contra", contravariant=True)
T_cov = TypeVar("T_cov", covariant=True)

T1 = TypeVar("T1")
T2 = TypeVar("T2")
T3 = TypeVar("T3")

S1 = TypeVar("S1")
S2 = TypeVar("S2")
S3 = TypeVar("S3")

num = TypeVar("num", int, float)
hashable = TypeVar("hashable", bound=Hashable)

P = ParamSpec("P")

# Argument was not given
NOT_GIVEN: Any = object()

# Alias to None, that can be typed as Any and therefore, accepted
# in any site that requires an arbitrary type like T.
EMPTY: Any = None

Raisable: TypeAlias = Exception | Type[Exception]


class Pred(Protocol[T_contra]):
    """
    Simple predicate function.
    """

    def __call__(self, x: T_contra, /) -> bool:
        ...


class BinOp(Protocol[a]):
    """
    Binary op (T, T) -> T
    """

    def __call__(self, x: a, y: a, /) -> a:
        ...


class FoldOp(Protocol[b, T_contra]):
    """
    Binary op (S, T) -> S

    This signature is often used in folds.
    """

    def __call__(self, x: b, y: T_contra, /) -> b:
        ...


INDEX_DOC = """index:
            Either a number that starts an infinite enumeration or a sequence
            of indexes that is passed as the first argument to func."""


#
# Utility functions
#
def to_callable(x):
    return x


def to_index_seq(index: int | bool | Iterable[a]) -> Iterable[a] | Iterable[int] | None:
    """
    Convert the index argument of many functions to a proper sequence.
    """
    if index is False or index is None or index is NOT_GIVEN:
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
