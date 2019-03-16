from types import FunctionType, MethodType, BuiltinFunctionType, BuiltinMethodType

FUNCTION_TYPES = FunctionType, MethodType, BuiltinFunctionType, BuiltinMethodType
identity = (lambda x: x)
true = (lambda *args, **kwargs: True)
false = (lambda *args, **kwargs: False)
__all__ = ['extract_function', 'extract_predicate_function']


def extract_function(f):
    """Convert argument to function.

    This *removes* sidekick's function wrappers (such as fn, for instance) and
    try to convert argument to a straightforward function value.

    This defines the following semantics:

    * Sidekick's fn, predicate, etc: extract the inner function.
    * None: return the identity function.
    * Functions, methods and other callables: returned as-is.
    """

    if isinstance(f, FUNCTION_TYPES):
        return f
    try:
        return f._sk_function_
    except AttributeError:
        if f is None:
            return identity
        elif callable(f):
            return f
        else:
            raise ValueError('cannot be interpreted as a function: %r' % f)


def extract_predicate_function(f):
    """
    Similar to :func:`extract_predicate`, but handle predicate functions.

    It define the following additional semantics:

    * Booleans are converted to functions that always return true or false.
    """

    if isinstance(f, FUNCTION_TYPES):
        return f
    try:
        return f._sk_function_
    except AttributeError:
        if f is None:
            return identity
        elif f is True:
            return true
        elif f is False:
            return false
        elif callable(f):
            return f
        else:
            raise ValueError('cannot be interpreted as a predicate function: %r' % f)


def sk_delegate(name, default, extra=None):
    """
    Delegate property to the _sk_function_ attribute of an fn object.

    If extra is defined, it must be a string pointing to a dictionary attribute
    in which the property might be stored. If the value exists on dictionary,
    it uses the value in the dictionary, otherwise it inspects the _sk_function_
    object, and finally uses the given default if all else fails.
    """

    if callable(default) and extra:
        def fget(self):
            names = getattr(self, extra)
            try:
                return names[name]
            except KeyError:
                return getattr(self._sk_function_, name, default())

    elif callable(default):
        def fget(self):
            return getattr(self._sk_function_, name, default())

    elif extra:
        def fget(self):
            names = getattr(self, extra)
            try:
                return names[name]
            except KeyError:
                return getattr(self._sk_function_, name, default)

    else:
        def fget(self):
            return getattr(self._sk_function_, name, default)

    return property(fget)
