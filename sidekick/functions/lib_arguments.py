from .core_functions import quick_fn
from .fn import fn


@fn
def set_defaults(func, *defaults):
    """
    Return a new function that replace all null arguments in the given positions
    by the provided default value.
    """

    if len(defaults) == 1:
        (x,) = defaults

        def fun(_x, *args, **kwargs):
            return func(x if _x is None else _x, *args, **kwargs)

    else:

        def fun(*args, **kwargs):
            args = iter(args)
            pre = (y if x is None else x for x, y in zip(args, defaults))
            return func(*pre, *args, **kwargs)

    return quick_fn(fun)


@fn
def value(fn_or_value, *args, **kwargs):
    """
    Evaluate argument, if it is a function or return it otherwise.

    Args:
        fn_or_value:
            Callable or some other value. If input is a callable, call it with
            the provided arguments and return. Otherwise, simply return.

    Examples:
        >>> value(42)
        42
        >>> value(lambda: 42)
        42
    """
    if callable(fn_or_value):
        return fn_or_value(*args, **kwargs)
    return fn_or_value
