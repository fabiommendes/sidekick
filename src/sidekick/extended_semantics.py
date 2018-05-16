from .fn import fn
from .placeholder import Placeholder
from .predicate import predicate

SK_FUNCTION_TYPES = (Placeholder, fn, predicate)


def as_func(f):
    "Extended function semantics for callable arguments."

    if isinstance(f, SK_FUNCTION_TYPES):
        return f._
    elif f is None:
        return lambda x: x
    elif callable(f):
        return f
    else:
        raise ValueError('cannot be interpreted as a function: %r' % f)


def as_key(f):
    "Extended function semantics for key arguments."

    if isinstance(f, SK_FUNCTION_TYPES):
        return f._
    elif f is None:
        return lambda x: x
    return f


def as_predicate_func(f):
    """
    Extended function semantics for argument that is expected to be a
    predicate.
    """

    if isinstance(f, SK_FUNCTION_TYPES):
        return f._
    elif callable(f):
        return f
    else:
        raise ValueError('cannot be interpreted as a predicate: %r' % f)
