from .._fn import fn, quick_fn


@fn
def set_defaults(func, *defaults):
    """
    Return a new function that replace all null arguments in the given positions
    by the provided default value.

    Examples:
        >>> my_filter =sk.fnull(sk.is_true, str.casefold)
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
