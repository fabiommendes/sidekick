from typing import Callable, Any

from .core_functions import quick_fn, to_callable
from .fn import fn
from .._toolz import compose as _compose, juxt as _juxt
from ..typing import Func, TYPE_CHECKING

if TYPE_CHECKING:
    from .. import api as sk  # noqa: F401
    from ..api import X, op  # noqa: F401


@fn
def compose(*funcs: Func) -> fn:
    """
    Create function that apply argument from right to left.

        compose(f, g, h, ...) ==> f << g << h << ...

    Example:
        >>> f = sk.compose((X + 1), (X * 2))
        >>> f(2)  # double than increment
        5

    See Also:
        :func:`pipe`
        :func:`pipeline`
    """
    return quick_fn(_compose(*map(to_callable, funcs)).__call__)


@fn
def pipeline(*funcs: Func) -> fn:
    """
    Similar to compose, but order of application is reversed.

        pipeline(f, g, h, ...) ==> f >> g >> h >> ...

    Example:
        >>> f = sk.pipeline((X + 1), (X * 2))
        >>> f(2)  # increment and double
        6

    See Also:
        :func:`pipe`
        :func:`compose`
    """
    return quick_fn(_compose(*map(to_callable, reversed(funcs))).__call__)


@fn
def pipe(data: Any, *funcs: Callable) -> Any:
    """
    Pipe a value through a sequence of functions.

    I.e. ``pipe(data, f, g, h)`` is equivalent to ``h(g(f(data)))`` or
    to ``data | f | g | h``, if ``f, g, h`` are fn objects.

    Examples:
        >>> from math import sqrt
        >>> sk.pipe(-4, abs, sqrt)
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
        >>> sk.thread(20, (op.div, 2), (op.mul, 4), (op.add, 2))
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
        >>> sk.rthread(2, (op.div, 20), (op.mul, 4), (op.add, 2))
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


@fn
def thread_if(data, *forms):
    """
    Similar to thread, but each form must be a tuple with (test, fn, ...args)
    and only pass the argument to fn if the boolean test is True.

    If test is callable, the current value to the callable to decide if fn must
    be executed or not.

    Like thread, Arguments are passed as tuples and the value is passed as the
    first argument.

    Examples:
        >>> sk.thread_if(20, (True, op.div, 2), (False, op.mul, 4), (sk.is_even, op.add, 2))
        12.0

    See Also:
        :func:`thread`
        :func:`rthread_if`
    """
    for i, form in enumerate(forms, 1):
        do_it, func, *args = form
        if callable(do_it):
            do_it = do_it(data)
        if do_it:
            try:
                data = func(data, *args)
            except Exception as ex:
                raise _thread_error(ex, func, (data, *args)) from ex

    return data


@fn
def rthread_if(data, *forms):
    """
    Similar to rthread, but each form must be a tuple with (test, fn, ...args)
    and only pass the argument to fn if the boolean test is True.

    If test is callable, the current value to the callable to decide if fn must
    be executed or not.

    Like rthread, Arguments are passed as tuples and the value is passed as the
    last argument.

    Examples:
        >>> sk.rthread_if(20, (True, op.div, 2), (False, op.mul, 4), (sk.is_even, op.add, 2))
        0.1

    See Also:
        :func:`thread`
        :func:`rthread_if`
    """
    for form in forms:
        do_it, func, *args = form
        if callable(do_it):
            do_it = do_it(data)
        if do_it:
            try:
                data = func(*args, data)
            except Exception as ex:
                raise _thread_error(ex, func, (*args, data)) from ex
    return data


@fn
def juxt(*funcs: Callable, first=None, last=None) -> fn:
    """
    Juxtapose several functions.

    Creates a function that calls several functions with the same arguments and
    return a tuple with all results.

    It return a tuple with the results of calling each function.
    If last=True or first=True, return the result of the last/first call instead
    of a tuple with all the elements.

    Examples:
        We can create an argument logger using either first/last=True

        >>> sqr_log = sk.juxt(print, (X * X), last=True)
        >>> sqr_log(4)
        4
        16

        Consume a sequence

        >>> pairs = sk.juxt(next, next)
        >>> nums = iter(range(10))
        >>> pairs(nums), pairs(nums)
        ((0, 1), (2, 3))
    """
    funcs = (to_callable(f) for f in funcs)

    if first is True:
        result_func, *funcs = funcs
        if not funcs:
            return fn(result_func)
        funcs = tuple(funcs)

        def juxt_first(*args, **kwargs):
            result = result_func(*args, **kwargs)
            for func in funcs:
                func(*args, **kwargs)
            return result

        return fn(juxt_first)

    if last is True:
        *funcs, result_func = funcs
        if not funcs:
            return fn(result_func)
        funcs = tuple(funcs)

        def juxt_last(*args, **kwargs):
            for func in funcs:
                func(*args, **kwargs)
            return result_func(*args, **kwargs)

        return fn(juxt_last)

    return fn(_juxt(*funcs))


def _thread_error(ex, func, args):
    args = ", ".join(map(repr, args))
    name = getattr(func, "__name__")
    msg = f"raised at {name}({args})" f"{type(ex).__name__}: {ex}"
    return ValueError(msg)
