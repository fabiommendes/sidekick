from functools import partial

from .extended_semantics import sk_delegate, extract_function

__all__ = ['fn']


class FnMeta(type):
    """Metaclass for the fn type"""

    _curry = None

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
        if cls._curry is None:
            from ..lib import curry
            cls._curry = curry
        return fn(cls._curry(func))


class fn(metaclass=FnMeta):  # noqa: N801
    """
    A function wrapper that enable functional programming superpowers.
    """

    __slots__ = '_sk_function_', '_extra'

    def __init__(self, func, **extra):
        fn._sk_function_.__set__(self, getattr(func, '_sk_function_', func))
        fn._extra.__set__(self, extra)

    def __repr__(self):
        try:
            return 'fn(%s)' % self._sk_function_.__name__
        except AttributeError:
            return 'fn(%r)' % self._sk_function_

    def __call__(self, *args, **kwargs):
        return self._sk_function_(*args, **kwargs)

    # Function composition operators
    def __ror__(self, other):
        return self._sk_function_(other)

    def __rrshift__(self, other):
        if isinstance(other, fn):
            other = other._sk_function_
        func = self._sk_function_
        return fn(lambda *args, **kw: func(other(*args, **kw)))

    def __rshift__(self, other):
        if isinstance(other, fn):
            other = other._sk_function_
        func = self._sk_function_
        return fn(lambda *args, **kw: other(func(*args, **kw)))

    __lshift__ = __rrshift__
    __rlshift__ = __rshift__

    # Make fn-functions behave nicely as methods
    def __get__(self, instance, cls=None):
        if instance is None:
            return self
        else:
            return partial(self._sk_function_, instance)

    # Function attributes and introspection
    __name__ = sk_delegate('__name__', 'lambda', '_extra')
    __doc__ = sk_delegate('__doc__', None, '_extra')
    __annotations__ = sk_delegate('__annotations__', dict, '_extra')
    __closure__ = sk_delegate('__closure__', None, '_extra')
    __code__ = sk_delegate('__code__', None, '_extra')
    __defaults__ = sk_delegate('__defaults__', None, '_extra')
    __globals__ = sk_delegate('__globals__', dict, '_extra')
    __kwdefaults__ = sk_delegate('__kwdefaults__', None, '_extra')
    __module__ = sk_delegate('__module__', '', '_extra')

    def __getattr__(self, attr):
        if attr in self._extra:
            return self._extra[attr]
        return getattr(self._sk_function_, attr)

    def __setattr__(self, attr, value):
        self._extra[attr] = value

    # Public methods
    def partial(self, *args, **kwargs):
        """
        Return a fn-function with all given positional and keyword arguments
        applied.
        """
        return fn(partial(self._sk_function_, *args, **kwargs))

    def apply_placeholder(self, *args, **kwargs):
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
        raise NotImplementedError


def as_fn(func):
    """
    Convert callable to an :cls:`fn` object.

    If func is already an :cls:`fn` instance, it is passed as is.
    """
    return func if isinstance(func, fn) else fn(func)


# ------------------------------------------------------------------------------
# Specialized fn classes. These classes provide better speed and static
# guarantees for fn() functions on non-function callables.
# ------------------------------------------------------------------------------
NOT_GIVEN = object()


class Fn1(fn):
    def __call__(self, x):
        return self._sk_function_(x)


class Fn1_(fn):
    def __call__(self, x, **kwargs):
        return self._sk_function_(x, **kwargs)


class Fn2(fn):
    def __call__(self, a, b=NOT_GIVEN):
        func = self._sk_function_
        if b is NOT_GIVEN:
            return Fn1(lambda b: func(a, b))
        return func(a, b)


class Fn2_(fn):
    def __call__(self, a, b=NOT_GIVEN, **kwargs):
        func = self._sk_function_
        if b is NOT_GIVEN:
            return Fn1_(lambda b: func(a, b, **kwargs))
        return func(a, b, **kwargs)


class Fn3(fn):
    def __call__(self, a, b=NOT_GIVEN, c=NOT_GIVEN):
        func = self._sk_function_
        if b is NOT_GIVEN:
            return Fn2(lambda b, c: func(a, b, c))
        elif c is NOT_GIVEN:
            return Fn1(lambda c: func(a, b, c))
        return func(a, b, c)


class Fn3_(fn):
    def __call__(self, a, b=NOT_GIVEN, c=NOT_GIVEN, **kwargs):
        func = self._sk_function_
        if b is NOT_GIVEN:
            return Fn1_(lambda b, c: func(a, b, c, **kwargs))
        elif c is NOT_GIVEN:
            return Fn1_(lambda c: func(a, b, c, **kwargs))
        return func(a, b, c, **kwargs)


#
# Predicate receivers
#
class Fn1P(Fn1_):
    def __call__(self, f, **kwargs):
        return super().__call__(extract_function(f), **kwargs)


class Fn2P(Fn2_):
    def __call__(self, f, x=NOT_GIVEN, **kwargs):
        return super().__call__(extract_function(f), x, **kwargs)


class Fn3P(Fn3_):
    def __call__(self, f, x=NOT_GIVEN, y=NOT_GIVEN, **kwargs):
        return super().__call__(extract_function(f), x, y, **kwargs)
