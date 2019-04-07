from typing import Mapping

import toolz

from ..core import fn, Function, Seq, extract_function

__all__ = ['accumulate', 'order_by', 'transform', 'transform_map',
           'products', 'sums', 'accumulate', 'scan', ]




@fn.annotate(2)
def order_by(key: Function, seq: Seq, *, indexed=False) -> list:
    """
    Order sequence by the given function.

    Args:
        key:
            Sort return values of the key function.
        seq:
            Sequence
        indexed (bool):
            If true, return list of indexed values.
    """
    if indexed:
        key = extract_function(key)
        seq = list(seq)
        seq.sort(key=lambda pair: key(pair[1]))
        return [i for i, x in seq]
    else:
        return sorted(seq, key=extract_function(key))


@fn.annotate(2)
def transform(funcs: Seq, seq: Seq) -> Seq:
    """
    Similar to :func:`zip_with`, but accepts only single argument functions. If the
    sequence of arguments is larger than the sequence of functions, the
    remaining values are returned unchanged.


    Args:
        funcs (iterable):
            An iterable of functions
        seq (iterable):
            The respective function arguments

    Returns:
        An iterator.
    """
    to_func = extract_function
    it = iter(seq)
    yield from (to_func(f)(x) for f, x in zip(funcs, it))
    yield from it


# noinspection PyIncorrectDocstring
def transform_map(funcs: Mapping, mapping: Mapping) -> Mapping:
    """
    Similar to transform, but instead of receiving a sequence of values, it
    expects maps. The function than apply each function in the map of functions
    to their corresponding values in the second argument.

    >>> transform_map({'foo': str.lower, 'ham': str.upper},
    ...           {'foo': 'Bar', 'ham': 'Spam', 'baz': 'Other'})
    {'foo': 'bar', 'ham': 'SPAM', 'baz': 'Other'}

    Args:
        funcs (Mapping):
            A mapping from arbitrary keys to functions.
        mapping (Mapping):
            Any mapping.

    Returns:
        dict
    """
    to_func = extract_function
    result = dict(mapping)
    for k, f in funcs:
        try:
            result[k] = to_func(f)(result[k])
        except KeyError:
            pass
    return result



