import random
import re
from collections import deque
from keyword import iskeyword

from hypothesis import strategies as st
from hypothesis.strategies._internal.core import (
    defines_strategy,
    defines_strategy_with_reusable_values,
)

from ..seq import singleton, Iter

IDENTIFIER_RE = re.compile(r"[^\d\W]\w*", re.ASCII)
PUBLIC_IDENTIFIER_RE = re.compile(r"[^\d\W_]\w*", re.ASCII)
SEQ_TYPES = (tuple, list, set, frozenset, deque)
AtomT = bool, int, float, complex, str, bytes, type(None), type(Ellipsis)


@defines_strategy
def atoms(which="basic", finite=False):
    """
    Return atomic Python types.

    Args:
        which:
            The category of atomic types to choose.

            'basic':
                Basic Python atomic literals (numbers, strings, bools, None, Ellipsis).
            'ordered':
                Exclude complex numbers, None, and Ellipsis since they do not have an
                ordering relation.
            'json':
                Only valid JSON data types (including valid Javascript numeric
                ranges)

        finite:
            Only yield finite numeric values (i.e., no NaN and infinities)
    """
    strategies = [
        st.booleans(),
        st.text(),
        st.floats(
            allow_nan=not finite and which != "json",
            allow_infinity=not finite and which != "json",
        ),
    ]
    add = strategies.append

    if which in ("basic", "ordered"):
        add(st.integers())
        add(st.just(None))
        add(st.binary())

    if which == "json":
        # See also:
        # https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference
        # /Global_Objects/Number/MIN_SAFE_INTEGER
        add(st.integers(min_value=-(2 ** 53 - 1), max_value=2 ** 53 - 1))
        add(st.just(None))

    if which == "basic":
        add(st.just(...))
        add(st.complex_numbers(allow_nan=not finite, allow_infinity=not finite))

    return st.one_of(*strategies)


@defines_strategy_with_reusable_values
def identifiers(allow_private=True, exclude=None):
    """
    Valid Python identifiers.
    """
    regex = IDENTIFIER_RE if allow_private else PUBLIC_IDENTIFIER_RE
    strategy = st.from_regex(regex, fullmatch=True).filter(lambda x: not iskeyword(x))
    if exclude:
        exclude = set(exclude)
        strategy = strategy.filter(lambda x: x not in exclude)
    return strategy


# noinspection PyShadowingNames
@defines_strategy
def kwargs(values=atoms(), **kwargs):
    """
    Create dictionaries that represent valid keyword arguments.
    """
    names = identifiers(**kwargs)
    pairs = st.tuples(names, values)
    return st.lists(pairs).map(dict)


# noinspection PyShadowingNames
def fcall(fn, args=None, kwargs=None):
    """
    Call function with given positional and keyword args.
    """

    if args == () or args is None:
        args = st.just(())
    elif isinstance(args, (tuple, list)):
        args = st.tuples(*args)

    if kwargs == {} or kwargs is None:
        kwargs = st.just({})
    elif isinstance(kwargs, dict):
        ks = list(kwargs.keys())
        kwargs = st.builds(lambda *xs: dict(zip(ks, xs)), *kwargs.values())

    return st.builds(lambda xs, kw: fn(*xs, **kw), args, kwargs)


def choice(values):
    """
    One value from a limited set.

    Args:
        values:
            Iterable with values that will be produced by strategy. Python enums
            are iterable and thus can be used as arguments for this strategy.

    Examples:
        >>> from hypothesis import strategies as st, given
        >>> from math import sin, cos
        >>> @given(choice([sin, cos]), st.floats(-1000, 1000))
        ... def check_range(fn, x):
        ...     assert -1 <= fn(x) <= 1
    """
    values = tuple(values)
    n_values = len(values)
    idxs = st.integers(n_values, 2 * n_values - 1)
    return idxs.map(lambda i: values[i % n_values])


def seqs(elements, **kwargs):
    """
    Returns Seq's of elements in sidekick sense.

    Seq can be real Python sequences or iterables.
    """
    return st.one_of(sequencies(elements, **kwargs), iterators(elements, **kwargs))


def seqs_n(elements, size=None, **kwargs):
    """
    Returns sequences alongside their sizes.

    Produces elements like ``seqs(elements, size=n, **kwargs)``, but returns
    tuples of (n, sequence). The sequence may be an iterator and therefore
    do not support len().
    """

    if size is not None:
        kwargs["min_size"] = kwargs["max_size"] = size

    funcs = (tuple, list, deque, iter, Iter, CustomIterable, CustomIterator)
    data = st.lists(elements, **kwargs)

    return st.builds(lambda fn, xs: (len(xs), fn(xs)), funcs, data)


def iterators(elements, **kwargs):
    """
    Map iter() function to sequences. Return an iterator that can be immediately
    used with the next() function.
    """
    return sequencies(elements, kind=list, **kwargs).map(iter)


def sequencies(elements, kind=SEQ_TYPES, *, size=None, **kwargs):
    """
    Create a sized container of uniform type based on lists strategy.

    It simply maps a lists strategy into a possibly different container.

    Args:
        elements:
            Strategy used to create elements of container.
        kind:
            List of types or single type of acceptable containers.
        size:
            Exact size of container.

    Keyword Args:
        It accepts all arguments of a lists strategy like min_size, max_size,
        unique and unique_by.

    Examples:
        >>> st.sized(st.integers())
        list(integers).map(container)
    """
    kind = tuple(singleton(kind))
    n_kinds = len(kind)
    if size is not None:
        kwargs["min_size"] = kwargs["max_size"] = size

    data = st.lists(elements, **kwargs)
    if n_kinds == 1:
        return data.map(kind[0])
    else:
        return st.builds(lambda xs, fn: fn(xs), data, choice(kind))


def funcs(ret, arity=None, *, pure=True, accept_kwargs=True, diversity=50):
    """
    Return random functions.

    Args:
        ret:
            Strategy for return value.
        arity:
            Optional function arity. Specify the number of arguments of created
            function.
        pure:
            If true, function will be "pure" in the sense that it will return the
            same values for the same arguments.
        accept_kwargs:
    """

    def funcs(iterable):
        outputs = deque((), diversity)
        results = {}

        def next_result():
            try:
                x = next(iterable)
            except StopIteration:
                return random.choice(outputs)
            else:
                outputs.append(x)
                return x

        def func(*args, **kwargs):
            if arity is not None:
                if len(args) != arity:
                    raise TypeError("invalid number of arguments")
            if kwargs and not accept_kwargs:
                raise TypeError("function does not accept keyword arguments.")

            if pure and not kwargs:
                key = (*args, *kwargs.items())
                try:
                    return results[key]
                except KeyError:
                    results[key] = out = next_result()
                    return out

            return next_result()

        return func

    return st.iterables(ret, min_size=diversity).map(funcs)


def preds(arity=None, **kwargs):
    """
    Alias to funcs(st.booleans())
    """
    return funcs(st.booleans(), arity, **kwargs)


class CustomIterable:
    def __init__(self, data):
        self.data = data

    def __iter__(self):
        yield from self.data


class CustomIterator:
    def __init__(self, data):
        self.data = iter(data)

    def __iter__(self):
        return self

    def __next__(self):
        return next(self.data)
