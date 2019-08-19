import math as _math

from .builtins import _execute_with, _create_fn_functions, abs, int, float, complex
from .core import fn


#
# We only define functions that differ from the math module
#
@fn.curry(2)
def copysign(src, target):
    """
    Return a float with the magnitude (absolute value) of source but the sign
    of target.

    Similar to math.copysign, but curried and with the order of arguments
    flipped.
    """
    return _math.copysign(target, src)


@fn.curry(2)
def fmod(denom, number):
    """
    Return number mod denom keeping the sign of the numerator. (number % denom
    returns the sign of denominator)

    Similar to math.fmod, but curried and with the order of arguments flipped.
    """
    return _math.fmod(number, denom)


@fn.curry(2)
def remainder(denom, number):
    """
    IEEE 754-style remainder of number with respect to denom. (Signal is chosen
    so remainder has the smaller absolute value).

    Similar to math.remainder, but curried and with the order of arguments
    flipped.
    """
    return _math.remainder(number, denom)


@fn.curry(2)
def logb(base, x):
    """
    Return logarithm of x in given base.
    """
    return _math.log(x, base)


@fn.curry(2)
def pow(n, x):
    """
    Raise x to power n.
    """
    return _math.pow(x, n)


@fn.curry(2)
def ldexp(n, x):
    """
    Return x * (2**n). This is essentially the inverse of function frexp().
    """
    return _math.ldexp(x, n)


#
# Patch module to include other functions
#
_execute_with(
    mod=_math,
    ns=globals(),
    arities={'gcd': 2, 'is_close': 2, 'atan2': 2, 'hypot': 2}) \
    (_create_fn_functions)
