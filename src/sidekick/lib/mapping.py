from sidekick.core.base_fn import extract_function
from ..core.fn import Fn2, Fn3


@Fn2
def map_values(func, mapping):
    """
    Apply function to all values of mapping.
    """
    func = extract_function(func)
    return {k: func(v) for k, v in mapping.items()}


@Fn2
def map_keys(func, mapping):
    """
    Apply function to all keys of mapping.
    """
    func = extract_function(func)
    return {func(k): v for k, v in mapping.items()}


@Fn3
def map_items(fk, fv, mapping):
    """
    Apply fk to keys of mapping and fv to its values.
    """
    fk = extract_function(fk)
    fv = extract_function(fv)
    return {fk(k): fv(v) for k, v in mapping.items()}
