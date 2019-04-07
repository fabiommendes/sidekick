import inspect
from functools import partial
from types import MappingProxyType as mappingproxy

from .fn_meta import FunctionMeta, extract_function, FUNCTION_ATTRIBUTES, make_xor, mixed_accessor, \
    lazy_property, arity
from .placeholder import compile_ast, call_node

__all__ = ['fn', 'as_fn']


class fn(metaclass=FunctionMeta):
    """
    Base class for function-like objects in Sidekick.
    """

    __slots__ = ("func", "__dict__", "__weakref__")
    __inner_function__: callable = property(lambda self: self.__wrapped__)
    _ok = _err = None
    args = ()
    keywords = mappingproxy({})

    #
    # Alternate constructors
    #
    @mixed_accessor
    def curry(self, n=None):
        """
        Return a curried version of function with arity n.

        If arity is not given, infer from function parameters.
        """
        return fn.curry(n, self.func)

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

    @classmethod
    def wraps(cls, func, fn_obj=None):
        """
        Creates a fn function that wraps another function.
        """
        if fn_obj is None:
            return lambda f: cls.wraps(func, f)
        if not isinstance(fn_obj, fn):
            fn_obj = fn(fn_obj)
        for attr in ('__name__', '__qualname__', '__doc__', '__annotations__'):
            value = getattr(func, attr, None)
            if value is not None:
                setattr(fn_obj, attr, value)
        return fn_obj

    @lazy_property
    def arity(self):
        return arity(self.func)

    @lazy_property
    def argspec(self):
        return inspect.getfullargspec(self.func)

    @lazy_property
    def signature(self):
        return inspect.Signature.from_callable(self.func)

    __wrapped__ = property(lambda self: self.func)

    def __init__(self, func, **kwargs):
        self.func = extract_function(func)
        self.__dict__ = dic = {}
        for k, v in kwargs.items():
            dic[FUNCTION_ATTRIBUTES.get(k, k)] = v

    def __repr__(self):
        try:
            func = self.func.__name__
        except AttributeError:
            func = repr(self.func)
        return f'{self.__class__.__name__}({func})'

    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)

    #
    # Function composition
    #
    def __rshift__(self, other):
        f = extract_function(other)
        g = self.__inner_function__
        return fn(lambda *args, **kw: f(g(*args, **kw)))

    def __rrshift__(self, other):
        f = extract_function(other)
        g = self.func
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
        # an value error because of the ambiguous interpretation. Should it be
        # piping or composition of predicates via an OR?
        if callable(f):
            raise AmbiguousOperation.default()
        else:
            return self.func(f)

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
            return partial(self.func, instance)

    #
    # Other python interfaces
    #
    def __getattr__(self, attr):
        return getattr(self.func, attr)

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
        ast = call_node(self.__inner_function__, *args, **kwargs)
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

    #
    # Wrapping
    #
    def result(self, *args, **kwargs):
        """
        Return a result instance after function call.

        Exceptions are converted to Err() cases.
        """
        try:
            return self._ok(self.func(*args, **kwargs))
        except Exception as exc:
            return self._err(exc)


# Slightly faster access for slotted object
# noinspection PyPropertyAccess
fn.__inner_function__ = fn.func


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

    def __repr__(self):
        try:
            func = self.func.__name__
        except AttributeError:
            func = repr(self.func)
        args = ', '.join(map(repr, self.args))
        kwargs = ', '.join(f'{k}={v!r}' for k, v in self.keywords.items())
        if not args:
            args = kwargs
        elif kwargs:
            args = ', '.join([args, kwargs])
        return f"<curry {func}({args})>"

    def __call__(self, *args, **kwargs):
        if not args and not kwargs:
            raise TypeError('curried function cannot be called without arguments')

        try:
            return self.func(*(self.args + args), **self.keywords, **kwargs)
        except TypeError:
            n = len(args)
            if n == 0 and not kwargs:
                msg = f'function receives between 1 and {self.arity} arguments'
                raise TypeError(msg)
            elif n >= self.arity:
                raise
            else:
                args = self.args + args
                update_arguments(self.keywords, kwargs)
                return Curried(self.func, self.arity - n, args, kwargs)

    def partial(self, *args, **kwargs):
        update_arguments(self.keywords, kwargs)
        n_args = self.arity - len(args)
        return Curried(self.func, n_args, args + self.args, kwargs)

    def rpartial(self, *args, **kwargs):
        update_arguments(self.keywords, kwargs)
        wrapped = self.func
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


def update_arguments(src, dest: dict):
    duplicate = set(src).intersection(dest)
    if duplicate:
        raise TypeError(f'duplicated keyword arguments: {duplicate}')
    dest.update(src)
    return dest
