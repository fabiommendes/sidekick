from functools import partial
from types import FunctionType, MethodType, BuiltinFunctionType, BuiltinMethodType

FUNCTION_TYPES = FunctionType, MethodType, BuiltinFunctionType, BuiltinMethodType
identity = lambda x: x
true = lambda *args, **kwargs: True
false = lambda *args, **kwargs: False


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
            try:
                return getattr(self._sk_function_, name)
            except KeyError:
                return default()

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


class FunctionMeta(type):
    """Metaclass for the fn type"""

    _curry = None

    def __new__(cls, name, bases, ns):
        ns.update(__doc__=sk_delegate("__doc__", None, "_extra"),
                  __module__=sk_delegate("__module__", "", "_extra"))
        return type.__new__(cls, name, bases, ns)

    def curried(cls, func):  # noqa: N805
        """
        Construct a curried fn function.
        """
        if cls._curry is None:
            from ..lib import curry

            cls._curry = curry
        return cls(cls._curry(func))


# noinspection PyProtectedMember
class SkFunction(metaclass=FunctionMeta):
    """
    Base class for function-like objects in Sidekick.
    """

    _sk_function_: callable
    _extra: dict

    __slots__ = ('_sk_function_', '_extra')

    def __init__(self, func, **kwargs):
        self._sk_function_ = func
        self._extra = kwargs

    def __repr__(self):
        cls_name = type(self).__name__
        try:
            return "%s(%s)" % (cls_name, self._sk_function_.__name__)
        except AttributeError:
            return "%s(%r)" % (cls_name, self._sk_function_)

    def __call__(self, *args, **kwargs):
        return self._sk_function_(*args, **kwargs)

    # Function composition
    def __rrshift__(self, other):
        if isinstance(other, SkFunction):
            other = other._sk_function_
        func = self._sk_function_
        return type(self)(lambda *args, **kw: func(other(*args, **kw)))

    def __rshift__(self, other):
        if isinstance(other, SkFunction):
            other = other._sk_function_
        func = self._sk_function_
        return type(self)(lambda *args, **kw: other(func(*args, **kw)))

    __lshift__ = __rrshift__
    __rlshift__ = __rshift__

    # Make fn-functions behave nicely as methods
    def __get__(self, instance, cls=None):
        if instance is None:
            return self
        else:
            return partial(self._sk_function_, instance)

    # Function attributes and introspection
    __name__ = sk_delegate("__name__", "lambda", "_extra")
    __annotations__ = sk_delegate("__annotations__", dict, "_extra")
    __closure__ = sk_delegate("__closure__", None, "_extra")
    __code__ = sk_delegate("__code__", None, "_extra")
    __defaults__ = sk_delegate("__defaults__", None, "_extra")
    __globals__ = sk_delegate("__globals__", dict, "_extra")
    __kwdefaults__ = sk_delegate("__kwdefaults__", None, "_extra")

    def __getattr__(self, attr):
        if attr in self._extra:
            return self._extra[attr]
        return getattr(self._sk_function_, attr)

    def __setattr__(self, attr, value):
        self._extra[attr] = value

    #
    # Partial operations
    #
    def partial(self, *args, **kwargs):
        """
        Return a fn-function with all given positional and keyword arguments
        applied.
        """
        func = self._sk_function_
        return type(self)(lambda *args_, **kwargs_:
                          func(*args, *args_, **kwargs, **kwargs_))

    def _apply_placeholder(self, *args, **kwargs):
        """
        Similar to partial, but with a few constraints:

        * Resulting function must be a function of a single positional argument.
        * Placeholder expressions are evaluated passing this single argument
          to the resulting function.

        Example:
            >>> from sidekick import placeholder as _
            >>> add = fn(lambda x, y: x + y)
            >>> g = add.apply_placeholder(_, 2 * _)
            >>> g(10)  # g(x) = x + 2 * x
            30

        Returns:
            fn
        """
        # args_placeholder = \
        #     any(isinstance(x, Placeholder) for x in args)
        # kwargs_placeholder = \
        #     any(isinstance(x, Placeholder) for x in kwargs.values())
        #
        # # Simple partial application with no placeholders
        # if not (args_placeholder or kwargs_placeholder):
        #     return fn(partial(self._sk_function_, *args, **kwargs))
        #
        # elif not kwargs_placeholder:
        #     func = self._sk_function_
        #     return fn(lambda x:
        #               func(*((x if e is placeholder else e) for e in args), **kwargs)
        #               )
        #
        # elif not args_placeholder:
        #     func = self._sk_function_
        #     return fn(lambda x:
        #               func(
        #                   *args,
        #                   **{k: (x if v is placeholder else v) for k, v in
        #                      kwargs.items()}))
        #
        # else:
        #     func = self._sk_function_
        #     return fn(lambda x:
        #               func(
        #                   *((x if e is placeholder else e) for e in args),
        #                   **{k: (x if v is placeholder else v) for k, v in
        #                      kwargs.items()}))
        ...


#
# Extended semantics
#
# noinspection PyProtectedMember
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
            raise ValueError("cannot be interpreted as a function: %r" % f)


# noinspection PyProtectedMember
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
            raise ValueError("cannot be interpreted as a predicate function: %r" % f)


# noinspection PyUnresolvedReferences,PyProtectedMember
def make_init(cls):
    set_func = cls._sk_function_.__set__
    set_extra = cls._extra.__set__

    def __init__(self, func, **extra):
        set_func(self, self._normalize_function(func))
        set_extra(self, extra)

    return __init__


SkFunction._normalize_function = staticmethod(extract_function)
SkFunction.__init__ = make_init(SkFunction)
