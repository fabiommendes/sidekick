import re
import textwrap
import typing as typ
from warnings import warn

from sidekick.typing import Func
from ..functions import fn

Fn1 = fn.annotate(1)
Fn2 = fn.annotate(2)
Fn3 = fn.annotate(3)
Fn1Opt = fn.annotate(1)
Fn2Opt = fn.annotate(2)
Fn3Opt = fn.annotate(3)

# from inflection import
NOT_GIVEN = object()
PredOrBool = typ.Union[Func, bool]

_fn1 = lambda func: Fn1(lambda st: func(st))
_fn2 = lambda func: Fn2(lambda x, st: func(st, x))
_fn3 = lambda func: Fn3(lambda x, y, st: func(st, x, y))
_fopt1 = lambda func: Fn1Opt(lambda st, **kwargs: func(st, **kwargs))
_fopt2 = lambda func: Fn2Opt(lambda x, st, **kwargs: func(st, x, **kwargs))
_fopt3 = lambda func: Fn3Opt(lambda x, y, st, **kwargs: func(st, x, y, **kwargs))

#
# Case control
#
capitalize = _fn1(str.capitalize)
casefold = _fn1(str.casefold)
lower = _fn1(str.lower)
swap_case = _fn1(str.swapcase)
title = _fn1(str.title)
upper = _fn1(str.upper)


#
#  Predicate queries
#
is_alnum = _fn1(str.isalnum)
is_alpha = _fn1(str.isalpha)
is_ascii = _fn1(getattr(str, "isascii", None))
is_decimal = _fn1(str.isdecimal)
is_digit = _fn1(str.isdigit)
is_identifier = _fn1(str.isidentifier)
is_lower = _fn1(str.islower)
is_numeric = _fn1(str.isnumeric)
is_printable = _fn1(str.isprintable)
is_space = _fn1(str.isspace)
is_title = _fn1(str.istitle)
is_upper = _fn1(str.isupper)


@fn
def ends_with(sub, st: str = NOT_GIVEN) -> PredOrBool:
    """
    Checks if string st ends with substring sub.

    If only one argument is given, return a predicate function.
    """
    if st is NOT_GIVEN:
        return fn(lambda x: x.endswith(sub))
    else:
        return st.endswith(sub)


@fn
def starts_with(sub, st: str = NOT_GIVEN) -> PredOrBool:
    """
    Checks if string st starts with substring sub.

    If only one argument is given, return a predicate function.
        """
    if st is NOT_GIVEN:
        return fn(lambda x: x.startswith(sub))
    else:
        return st.startswith(sub)


# Aliases for Python API function names
endswith = ends_with
startswith = starts_with

#
# Whitespace control
#
trim = _fn1(str.strip)
ltrim = _fn1(str.lstrip)
rtrim = _fn1(str.rstrip)
dedent = _fn1(textwrap.dedent)
indent = _fn1(textwrap.indent)

#
# Alignment
#
center = _fopt2(str.center)
rjust = _fopt2(str.rjust)
ljust = _fopt2(str.ljust)
zfill = _fn2(str.zfill)
wrap_lines = _fn2(textwrap.wrap)
wrap = _fn2(textwrap.fill)
shorten = _fopt2(textwrap.shorten)


#
# Discover sub-strings
#
def _mk(func, doc=None, name=None):
    def function(sub, st, *, start=0, end=None):
        return func(st, sub, start=start, end=end)

    function.__name__ = function.__qualname__ = name or func.__name__
    function.__doc__ = doc or func.__doc__
    return Fn2Opt(function)


count = _mk(str.count, doc="Count the number of occurrences of sub in st.")
index = _mk(
    str.index,
    doc="""
Return the lowest index in S where substring sub is found,
such that sub is contained within S[start:end].  Optional
arguments start and end are interpreted as in slice notation.

Raises ValueError when the substring is not found.
""",
)
rindex = _mk(
    str.rindex,
    doc="""
Return the highest index in S where substring sub is found,
such that sub is contained within S[start:end].  Optional
arguments start and end are interpreted as in slice notation.

Raises ValueError when the substring is not found.
""",
)
find = _mk(str.find, doc="Like index, but return -1, if string is not found.")
rfind = _mk(str.rfind, doc="Like rindex, but return -1, if string is not found.")

#
# Transformations
#
encode = _fopt2(str.encode)
expandtabs = _fopt2(str.expandtabs)
translate = _fopt2(str.translate)
maketrans = _fopt2(str.maketrans)
replace = _fopt3(str.replace)

#
# Substrings
#
lstrip = _fn2(str.lstrip)
rstrip = _fn2(str.rstrip)
strip = _fn2(str.strip)


#
# Formatting
#
def format_with(*args, **kwargs):
    """
    Return a function that performs the given positional or keyword formatting
    using the str.format method on its argument.
    """
    return fn(lambda st: st.format(*args, **kwargs))


def format_c(*args, **kwargs):
    """
    Like :func:`format_with`, but uses the C-style string interpolation with the
    mod operator "%".
    """
    if args:
        if kwargs:
            msg = "cannot declare positional and keyword arguments at the same time."
            raise TypeError(msg)
        return fn(lambda st: st % args)
    else:
        return fn(lambda st: st % kwargs)


@Fn2
def format_map(mapping, st):
    """
    Format string st with given map.
    """
    return st.format_map(mapping)


#
# Splitting
#
partition = _fn2(str.partition)
rpartition = _fn2(str.rpartition)
rsplit = _fopt2(str.rsplit)
split = _fopt2(str.split)
rwords = _fn1(str.rsplit)
words = _fn1(str.split)
split_lines = _fn1(str.splitlines)

#
# Joining
#
join = Fn2(str.join)

#
# Regular expressions
#
re_search = Fn2Opt(re.search)
re_match = Fn2Opt(re.match)
re_fullmatch = Fn2Opt(re.fullmatch)
re_split = Fn2Opt(re.split)
re_findall = Fn2Opt(re.findall)
re_finditer = Fn2Opt(re.finditer)
re_sub = Fn3Opt(re.sub)
re_subn = Fn3Opt(re.subn)
re_escape = _fn1(re.escape)


# ------------------------------------------------------------------------------
# Deprecated functions
# ------------------------------------------------------------------------------


def deprecated(name, **reasons):
    k, v = reasons.popitem()
    if k == "alias_of":
        fname = getattr(v, "__name__", "<lambda>")
        msg = f"Function {name} was replaced by {fname}."
        return lambda *args, **kwargs: warn(msg) and v(*args, **kwargs)
    else:
        raise TypeError


isalnum = deprecated("isalnum", alias_of=is_alnum)
isalpha = deprecated("isalpha", alias_of=is_alpha)
isascii = deprecated("isascii", alias_of=is_ascii)
isdecimal = deprecated("isdecimal", alias_of=is_decimal)
isdigit = deprecated("isdigit", alias_of=is_digit)
isidentifier = deprecated("isidentifier", alias_of=is_identifier)
islower = deprecated("islower", alias_of=is_lower)
isnumeric = deprecated("isnumeric", alias_of=is_numeric)
isprintable = deprecated("isprintable", alias_of=is_printable)
isspace = deprecated("isspace", alias_of=is_space)
istitle = deprecated("istitle", alias_of=is_title)
isupper = deprecated("isupper", alias_of=is_upper)
splitlines = deprecated("splitlines", alias_of=split_lines)
swapcase = deprecated("swapcase", alias_of=swap_case)
