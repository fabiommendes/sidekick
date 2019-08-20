import re
from keyword import iskeyword

from hypothesis import strategies as st

IDENTIFIER_RE = re.compile(r'[^\d\W]\w*', re.ASCII)
PUBLIC_IDENTIFIER_RE = re.compile(r'[^\d\W_]\w*', re.ASCII)


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


def atoms():
    """
    Return atomic Python types.
    """
    return st.one_of(
        st.text(),
        st.floats(allow_nan=False),
        st.integers(),
    )


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
