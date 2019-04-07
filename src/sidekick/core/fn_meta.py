import inspect
from copy import copy

from types import FunctionType, MethodType, BuiltinFunctionType, BuiltinMethodType

FUNCTION_TYPES = FunctionType, MethodType, BuiltinFunctionType, BuiltinMethodType
FUNCTION_ATTRIBUTES = {
    'doc': '__doc__',
    'name': '__name__',
    'annotations': '__annotations__',
    'closure': '__closure__',
    'code': '__code__',
    'defaults': '__defaults__',
    'globals': '__globals__',
    'kwdefaults': '__kwdefaults__',
}

identity = lambda x: x


class FunctionMeta(type):
    """Metaclass for the fn type"""

    _curry = None

    def __new__(mcs, name, bases, ns):
        ns.update(
            __doc__=lazy_property(lambda x: x.__getattr__('__doc__')),
            __module__=lazy_property(lambda x: x.__getattr__('__module__')),
        )
        return type.__new__(mcs, name, bases, ns)

    def __rshift__(self, other):
        if isinstance(other, self):
            return other

        try:
            func = extract_function(other)
        except TypeError:
            return NotImplementedError
        else:
            return self(func)

    __lshift__ = __rlshift__ = __rrshift__ = __rshift__


#
# Utility types
#
class lazy_property:
    """
    Lazy property accessor.

    Used to mirror wrapped function properties.
    """

    __slots__ = 'func'

    def __init__(self, func):
        self.func = func

    def __get__(self, instance, cls=None):
        if instance is None:
            return self
        return self.func(instance)


class mixed_accessor:
    """
    Descriptor with different class and an instance implementations.
    """
    __slots__ = ('_cls', '_instance')

    def __init__(self, instance=None, cls=None):
        self._cls = cls
        self._instance = instance
        if cls:
            self._cls = classmethod(cls).__get__
        if instance:
            self._instance = instance.__get__

    def classmethod(self, func):
        new = copy(self)
        new._cls = classmethod(func).__get__
        return new

    def instancemethod(self, func):
        new = copy(self)
        new._instance = func.__get__
        return new

    def __get__(self, instance, cls=None):
        if instance is None:
            return self._cls(cls)
        else:
            return self._instance(instance)

    def __set__(self, instance, value):
        raise TypeError


#
# Utility functions
#
def make_xor(f, g):
    """
    Compose functions in a short-circuit version of xor using the following
    table:

    +--------+--------+-------+
    | A      | B      | A^B   |
    +--------+--------+-------+
    | truthy | truthy | not B |
    +--------+--------+-------+
    | truthy | falsy  | A     |
    +--------+--------+-------+
    | falsy  | truthy | B     |
    +--------+--------+-------+
    | falsy  | falsy  | B     |
    +--------+--------+-------+
    """

    def xor(*args, **kwargs):
        a = f(*args, **kwargs)
        if a:
            b = g(*args, **kwargs)
            return not b if b else a
        else:
            return g(*args, **kwargs)

    return xor


def arity(func):
    """
    Return arity of a function.
    """
    if hasattr(func, 'arity'):
        return func.arity

    spec = inspect.getfullargspec(func)
    if spec.varargs or spec.varkw or spec.kwonlyargs:
        raise TypeError("cannot curry a variadic function")
    return len(spec.args)


# noinspection PyProtectedMember
def extract_function(func):
    """Convert argument to function.

    This *removes* sidekick's function wrappers (such as fn, for instance) and
    try to convert argument to a straightforward function value.

    This defines the following semantics:

    * Sidekick's fn, predicate, etc: extract the inner function.
    * None: return the identity function.
    * Functions, methods and other callables: returned as-is.
    """

    if isinstance(func, FUNCTION_TYPES):
        return func
    try:
        return func.__inner_function__
    except AttributeError:
        if func is None:
            return identity
        elif callable(func):
            return func
        else:
            raise TypeError("cannot be interpreted as a function: %r" % func)
