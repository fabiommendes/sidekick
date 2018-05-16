from functools import partial

from .placeholder import Placeholder, placeholder


def prop_delegate(name, default):
    "Delegate property to the _ attribute of an fn object."

    if callable(default):
        def fget(self):
            return getattr(self._, name, default())
    else:
        def fget(self):
            return getattr(self._, name, default)
    return property(fget)


class FnMeta(type):
    "Metaclass for the fn type"

    def __rshift__(self, other):
        return fn(other)

    def __getitem__(self, other):
        print(other)
        if isinstance(other, tuple):
            func, *args = other
            return fn(func).partial(*args)
        return fn(other)

    def curried(cls, func):  # noqa: N805
        """
        Construct a curried fn function.
        """
        try:
            curry = cls._curry
        except AttributeError:
            from .lib_functions import curry
            cls._curry = curry
        return fn(curry(func))


class fn(metaclass=FnMeta):  # noqa: N801
    """
    A function wrapper that enable functional programming superpowers.
    """

    def __init__(self, function, doc=None):
        if isinstance(function, Placeholder):
            function = function._
        self._ = function
        if doc is not None:
            self.__doc__ = doc
        else:
            self.__doc__ = getattr(function, '__doc__', None)

    def __repr__(self):
        try:
            return 'fn(%s)' % self._.__name__
        except AttributeError:
            return 'fn(%r)' % self._

    def __call__(self, *args, **kwargs):
        return self._(*args, **kwargs)

    # Pipe operator
    def __ror__(self, other):
        return self._(other)

    # Function composition operators
    def __rrshift__(self, other):
        if isinstance(other, fn):
            other = other._
        function = self._
        return fn(lambda *args, **kw: function(other(*args, **kw)))

    def __rshift__(self, other):
        if isinstance(other, fn):
            other = other._
        function = self._
        return fn(lambda *args, **kw: other(function(*args, **kw)))

    __lshift__ = __rrshift__
    __rlshift__ = __rshift__

    # Partial application
    def __getitem__(self, item):
        if not isinstance(item, tuple):
            item = item,
        return self.partial(*item)

    # Make fn-functions behave nicely as methods
    def __get__(self, instance, cls=None):
        if instance is None:
            return self
        else:
            return partial(self._, instance)

    # Function attributes and introspection
    __name__ = prop_delegate('__name__', 'lambda')
    __annotations__ = prop_delegate('__annotations__', dict)
    __closure__ = prop_delegate('__closure__', None)
    __code__ = prop_delegate('__code__', None)
    __defaults__ = prop_delegate('__defaults__', None)
    __globals__ = prop_delegate('__globals__', dict)
    __kwdefaults__ = prop_delegate('__kwdefaults__', None)
    __module__ = prop_delegate('__module__', '')

    def __getattr__(self, attr):
        return getattr(self._, attr)

    # Public methods
    def partial(self, *args, **kwargs):
        """
        Return a fn-function with all given positional and keyword arguments
        applied.
        """

        args_placeholder = \
            any(isinstance(x, Placeholder) for x in args)
        kwargs_placeholder = \
            any(isinstance(x, Placeholder) for x in kwargs.values())

        # Simple partial application with no placeholders
        if not (args_placeholder or kwargs_placeholder):
            return fn(partial(self._, *args, **kwargs))

        elif not kwargs_placeholder:
            func = self._
            return fn(lambda x:
                      func(*((x if e is placeholder else e) for e in args), **kwargs)
                      )

        elif not args_placeholder:
            func = self._
            return fn(lambda x:
                      func(
                          *args,
                          **{k: (x if v is placeholder else v) for k, v in
                             kwargs.items()}
                      )
                      )

        else:
            func = self._
            return fn(lambda x:
                      func(
                          *((x if e is placeholder else e) for e in args),
                          **{k: (x if v is placeholder else v) for k, v in
                             kwargs.items()}
                      )
                      )
