import re
from keyword import iskeyword

from hypothesis import strategies as st

IDENTIFIER_RE = re.compile(r"[^\d\W]\w*", re.ASCII)
PUBLIC_IDENTIFIER_RE = re.compile(r"[^\d\W_]\w*", re.ASCII)

AtomT = bool, int, float, complex, str, bytes, type(None), type(Ellipsis)


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
        # https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Number/MIN_SAFE_INTEGER
        add(st.integers(min_value=-(2 ** 53 - 1), max_value=2 ** 53 - 1))
        add(st.just(None))

    if which == "basic":
        add(st.just(...))
        add(st.complex_numbers(allow_nan=not finite, allow_infinity=not finite,))

    return st.one_of(*strategies)


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
    values = list(values)
    return st.integers(min_value=0, max_value=len(values) - 1).map(values.__getitem__)
