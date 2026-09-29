from typing import overload

from hypothesis import strategies as st
from hypothesis.strategies._internal.core import defines_strategy

from .maybe import Maybe, Nothing
from .result import Result
from .util import a, err


@defines_strategy()
def maybes(
    value: st.SearchStrategy[a], nullable_just: bool = False
) -> st.SearchStrategy[Maybe[a]]:
    """
    Return maybes for the given value.
    """
    just = Maybe.from_value if nullable_just else Maybe.from_optional
    return st.one_of(st.just(Nothing), value.map(just))  # type: ignore


@overload
def results(value: st.SearchStrategy[a]) -> st.SearchStrategy[Result[str, a]]:
    ...


@overload
def results(
    value: st.SearchStrategy[a], err: st.SearchStrategy[err]
) -> st.SearchStrategy[Result[err, a]]:
    ...


@defines_strategy()
def results(value, err=st.text()):
    """
    Return results for the given value/error.
    """
    return st.one_of(err.map(Result.from_error), value.map(Result.from_value))  # type: ignore
