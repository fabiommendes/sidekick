import inspect
from functools import partial, wraps

from types import MappingProxyType as mappingproxy

from .fn_meta import FunctionMeta, extract_function, FUNCTION_ATTRIBUTES, make_xor, mixed_accessor, \
    lazy_property, arity
from .placeholder import Call, Cte, to_ast, compile_ast

__all__ = ['fn', 'as_fn']


class fn(metaclass=FunctionMeta):
    """
    Base class for function-like objects in Sidekick.
    """

    __slots__ = ("__dict__", "__wrapped__")
    __inner_function__: callable = property(lambda self: self.__wrapped__)

    #
    # Alternate constructors
    #
    @mixed_accessor
    def curry(self, n=None):
        """
        Return a curried version of function with arity n.

        If arity is not given, infer from function parameters.
        """
        return fn.curry(n, self.__wrapped__)

    @curry.classmethod
    def curry(cls, arity, func=None, **kwargs):
        """
        Return a curried function with given arity.
        """
        if func is None:
            return lambda f: fn.curry(arity, f, **kwargs)
        if isinstance(arity, int):
            return Curried(func, arity)
        else:
            raise NotImplementedError

    # TODO: rename annotate to curry
    annotate = curry

    @classmethod
    def wraps(cls, func):
        """
        Creates a fn function that wraps another function.
        """
        return lambda impl: cls(wraps(func)(impl))

    @lazy_property
    def arity(self):
        return arity(self.__wrapped__)

    @lazy_property
    def argspec(self):
        return inspect.getfullargspec(self.__wrapped__)

    @lazy_property
    def signature(self):
        return inspect.Signature.from_callable(self.__wrapped__)

    def __init__(self, func, **kwargs):
        self.__wrapped__ = extract_function(func)
        self.__dict__ = dic = {}
        for k, v in kwargs.items():
            dic[FUNCTION_ATTRIBUTES.get(k, k)] = v

    def __repr__(self):
        cls_name = type(self).__name__
        try:
            func = self.__wrapped__.__name__
        except AttributeError:
            func = repr(self.__wrapped__)
        return f"{cls_name}({func})"

    def __call__(self, *args, **kwargs):
        return self.__wrapped__(*args, **kwargs)

    #
    # Function composition
    #
    def __rshift__(self, other):
        f = extract_function(other)
        g = self.__inner_function__
        return fn(lambda *args, **kw: f(g(*args, **kw)))

    def __rrshift__(self, other):
        f = extract_function(other)
        g = self.__wrapped__
        return fn(lambda *args, **kw: g(f(*args, **kw)))

    __lshift__ = __rrshift__
    __rlshift__ = __rshift__

    #
    # Predicate and boolean algebra
    #
    def __xor__(self, g):
        f = self.__inner_function__
        g = extract_function(g)
        return fn(make_xor(f, g))

    def __rxor__(self, f):
        f = extract_function(f)
        g = self.__inner_function__
        return fn(make_xor(f, g))

    def __or__(self, g):
        f = self.__inner_function__
        g = extract_function(g)
        return fn(lambda *xs, **kw: f(*xs, **kw) or g(*xs, **kw))

    def __ror__(self, f):
        # ror can also be interpreted as arg | func. If lhs is a callable, raise
        # an value error because of the ambiguous interpretation
        if callable(f):
            raise AmbiguousOperation.default()
        else:
            return self.__wrapped__(f)

    def __and__(self, g):
        f = self.__inner_function__
        g = extract_function(g)
        return fn(lambda *xs, **kw: f(*xs, **kw) and g(*xs, **kw))

    def __rand__(self, f):
        f = extract_function(f)
        g = self.__inner_function__
        return fn(lambda *xs, **kw: f(*xs, **kw) and g(*xs, **kw))

    def __invert__(self):
        f = self.__inner_function__
        return fn(lambda *xs, **kw: not f(*xs, **kw))

    def __lt__(self, other):
        return self.__inner_function__(other)

    #
    # Descriptor interface
    #
    def __get__(self, instance, cls=None):
        if instance is None:
            return self
        else:
            return partial(self.__inner_function__, instance)

    #
    # Other python interfaces
    #
    def __getattr__(self, attr):
        return getattr(self.__wrapped__, attr)

    #
    # Partial application
    #
    def partial(self, *args, **kwargs):
        """
        Return a fn-function with all given positional and keyword arguments
        applied.
        """
        func = self.__inner_function__
        return fn(
            lambda *xs, **kw: func(*args, *xs, **kwargs, **kw)
        )

    def rpartial(self, *args, **kwargs):
        """
        Like partial, but fill positional arguments from right to left.
        """
        func = self.__inner_function__
        return fn(
            lambda *xs, **kw: func(*xs, *args, **update_arguments(kwargs, kw))
        )

    def single(self, *args, **kwargs):
        """
        Similar to partial, but with a few constraints:

        * Resulting function must be a function of a single positional argument.
        * Placeholder expressions are evaluated passing this single argument
          to the resulting function.

        Example:
            >>> add = fn(lambda x, y: x + y)
            >>> g = add.single(_, 2 * _)
            >>> g(10)  # g(x) = x + 2 * x
            30

        Returns:
            fn
        """
        args = tuple(map(to_ast, args))
        kwargs = {k: to_ast(v) for k, v in kwargs.items()}
        ast = Call(Cte(self.__inner_function__), args, kwargs)
        return compile_ast(ast)

    def splice(self, args, kwargs=None):
        """
        Splice sequence of arguments in function.

        Keywords can be passed as a second optional argument.
        """
        if kwargs is None:
            return self.__inner_function__(*args)
        else:
            return self.__inner_function__(*args, **kwargs)

    def splice_kw(self, kwargs):
        """
        Splice keywords arguments in function.
        """
        return self.__inner_function__(**kwargs)


# Slightly faster access for slotted object
# noinspection PyPropertyAccess
fn.__inner_function__ = fn.__wrapped__


#
# Specialized classes: curried
#
class Curried(fn):
    """
    Curried function with known arity.
    """
    __slots__ = ('args', 'arity', 'keywords')

    @property
    def __inner_function__(self):
        return self

    def __init__(self, func: callable, arity: int,
                 args: tuple = (),
                 keywords: dict = mappingproxy({}), **kwargs):
        super().__init__(func, **kwargs)
        self.args = args
        self.keywords = keywords
        self.arity = arity

    def __call__(self, *args, **kwargs):
        if not args and not kwargs:
            raise TypeError('curried function cannot be called without arguments')

        try:
            return self.__wrapped__(*(self.args + args), **self.keywords, **kwargs)
        except TypeError:
            n = len(args)
            if n == 0:
                msg = f'function receives between 1 and {self.arity} arguments'
                raise TypeError(msg)
            elif n >= self.arity:
                raise
            else:
                args = self.args + args
                update_arguments(self.keywords, kwargs)
                return Curried(self.__wrapped__, self.arity - n, args, kwargs)

    def partial(self, *args, **kwargs):
        update_arguments(self.keywords, kwargs)
        n_args = self.arity - len(args)
        return Curried(self.__wrapped__, n_args, args + self.args, kwargs)

    def rpartial(self, *args, **kwargs):
        update_arguments(self.keywords, kwargs)
        wrapped = self.__wrapped__
        if self.args:
            wrapped = partial(wrapped, args)
        return fn(wrapped).rpartial(*args, **kwargs)


#
# Utility functions and types
#
def as_fn(func):
    """
    Convert callable to an :cls:`fn` object.

    If func is already an :cls:`fn` instance, it is passed as is.
    """
    return func if isinstance(func, fn) else fn(func)


class AmbiguousOperation(ValueError):
    """
    Raised when calling (lhs | func) for a callable lhs.
    """

    @classmethod
    def default(cls):
        return cls(
            'do you want to compose predicates or pass argument to function?'
            '\nUse `fn(lhs) | func` in the former and `lhs > func` in the latter.')


def update_arguments(src, dest):
    duplicate = set(src).intersection(dest)
    if duplicate:
        raise TypeError(f'duplicated keyword arguments: {duplicate}')
    dest.update(src)
    return dest
