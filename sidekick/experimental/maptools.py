from ..functions import fn, to_callable


@fn.annotate(2)
def map_values(func, mapping):
    """
    Apply function to all values of mapping.
    """
    func = to_callable(func)
    return {k: func(v) for k, v in mapping.items()}


@fn.annotate(2)
def map_keys(func, mapping):
    """
    Apply function to all keys of mapping.
    """
    func = to_callable(func)
    return {func(k): v for k, v in mapping.items()}


@fn.annotate(3)
def map_items(fk, fv, mapping):
    """
    Apply fk to keys of mapping and fv to its values.
    """
    fk = to_callable(fk)
    fv = to_callable(fv)
    return {fk(k): fv(v) for k, v in mapping.items()}
