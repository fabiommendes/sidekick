from typing import Callable, Any

from .._fn import fn, quick_fn, extract_function
from .._toolz import compose as _compose
from ..typing import Func


@fn
def compose(*funcs: Func) -> fn:
    """
    Create function that apply argument from right to left.

        compose(f, g, h, ...) ==> f << g << h << ...

    Example:
        >>> f = compose((X + 1), (X * 2))
        >>> f(2)  # double than increment
        5

    See Also:
        :func:`pipe`
        :func:`pipeline`
    """
    return quick_fn(_compose(*map(extract_function, funcs)).__call__)


@fn
def pipeline(*funcs: Func) -> fn:
    """
    Similar to compose, but order of application is reversed, i.e.:

        pipeline(f, g, h, ...) ==> f >> g >> h >> ...

    Example:
        >>> f = pipeline((X + 1), (X * 2))
        >>> f(2)  # increment and double
        6

    See Also:
        :func:`pipe`
        :func:`compose`
    """
    return quick_fn(_compose(*map(extract_function, reversed(funcs))).__call__)


@fn
def pipe(data: Any, *funcs: Callable) -> Any:
    """
    Pipe a value through a sequence of functions.

    I.e. ``pipe(data, f, g, h)`` is equivalent to ``h(g(f(data)))`` or
    to ``data | f | g | h``, if ``f, g, h`` are fn objects.

    Examples:
        >>> from math import sqrt
        >>> pipe(-4, abs, sqrt)
        2.0

    See Also:
        :func:`pipeline`
        :func:`compose`
        :func:`thread`
        :func:`rthread`
    """
    if funcs:
        for func in funcs:
            data = func(data)
        return data
    else:
        return lambda *args: pipe(data, *args)


@fn
def thread(data, *forms):
    """
    Similar to pipe, but accept extra arguments to each function in the
    pipeline.

    Arguments are passed as tuples and the value is passed as the
    first argument.

    Examples:
        >>> thread(20, (op.div, 2), (op.mul, 4), (op.add, 2))
        42.0

    See Also:
        :func:`pipe`
        :func:`rthread`
    """
    for form in forms:
        if isinstance(form, tuple):
            func, *args = form
        else:
            func = form
            args = ()
        data = func(data, *args)
    return data


@fn
def rthread(data, *forms):
    """
    Like thread, but data is passed as last argument to functions,
    instead of first.

    Examples:
        >>> rthread(2, (op.div, 20), (op.mul, 4), (op.add, 2))
        42.0

    See Also:
        :func:`pipe`
        :func:`thread`
    """
    for form in forms:
        if isinstance(form, tuple):
            func, *args = form
        else:
            func = form
            args = ()
        data = func(*args, data)
    return data
