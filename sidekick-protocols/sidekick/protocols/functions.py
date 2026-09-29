from __future__ import annotations

from typing import (
    overload,
    Any,
    Protocol,
    Annotated as Bind,
    Callable as Fn,
)
from .util import (
    a_contra as a,
    b_contra as b,
    c_contra as c,
    d_contra as d,
    e_contra as e,
    r_co as r,
    a as a_,
)


class BinOp(Protocol):
    """
    Type-stable binary operator.
    """

    def __call__(self, x: a_, y: a_, /) -> a_:
        raise NotImplementedError


class Curry1(Protocol[a, r]):
    """
    One-argument curried function with keyword arguments.
    """

    @overload
    def __call__(self, x: a, /, **kwargs) -> r:
        ...

    @overload
    def __call__(self, **kwargs) -> Fn[[a], r]:
        ...

    def __call__(self, x, **kwargs):
        raise NotImplementedError


class Curry2(Protocol[a, b, r]):
    """
    Two-argument curried function with keyword arguments.
    """

    @overload
    def __call__(self, x: a, y: b, /, **kwargs) -> Any:
        ...

    @overload
    def __call__(self, x: a, /, **kwargs) -> Fn[[b], Any]:
        ...

    @overload
    def __call__(self, **kwargs) -> Fn[[a, b], Any]:
        ...

    def __call__(self, x, y, **kwargs):
        raise NotImplementedError


class Curry3(Protocol[a, b, c, r]):
    """
    3-argument curried function with keyword arguments.
    """

    @overload
    def __call__(self, x: a, y: b, z: c, /, **kwargs) -> Any:
        ...

    @overload
    def __call__(self, x: a, y: b, /, **kwargs) -> Fn[[c], Any]:
        ...

    @overload
    def __call__(self, x: a, /, **kwargs) -> Fn[[b, c], Any]:
        ...

    @overload
    def __call__(self, **kwargs) -> Fn[[a, b, c], Any]:
        ...

    def __call__(self, x, y, **kwargs):
        raise NotImplementedError


class Curry4(Protocol[a, b, c, d, r]):
    """
    4-argument curried function with keyword arguments.
    """

    @overload
    def __call__(self, x: a, y: b, z: c, w: d, /, **kwargs) -> Any:
        ...

    @overload
    def __call__(self, x: a, y: b, z: c, /, **kwargs) -> Fn[[d], Any]:
        ...

    @overload
    def __call__(self, x: a, y: b, /, **kwargs) -> Fn[[c, d], Any]:
        ...

    @overload
    def __call__(self, x: a, /, **kwargs) -> Fn[[b, c, d], Any]:
        ...

    @overload
    def __call__(self, **kwargs) -> Fn[[a, b, c, d], Any]:
        ...

    def __call__(self, x, y, **kwargs):
        raise NotImplementedError


class Curry5(Protocol[a, b, c, d, e, r]):
    """
    5-argument curried function with keyword arguments.
    """

    @overload
    def __call__(self, x: a, y: b, z: c, w: d, ww: e, /, **kwargs) -> Any:
        ...

    @overload
    def __call__(self, x: a, y: b, z: c, w: d, /, **kwargs) -> Fn[[e], Any]:
        ...

    @overload
    def __call__(self, x: a, y: b, z: c, /, **kwargs) -> Fn[[d, e], Any]:
        ...

    @overload
    def __call__(self, x: a, y: b, /, **kwargs) -> Fn[[c, d, e], Any]:
        ...

    @overload
    def __call__(self, x: a, /, **kwargs) -> Fn[[b, c, d, e], Any]:
        ...

    @overload
    def __call__(self, **kwargs) -> Fn[[a, b, c, d, e], Any]:
        ...

    def __call__(self, x, y, **kwargs):
        raise NotImplementedError
