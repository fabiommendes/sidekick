import inspect
from functools import singledispatch

from ..typing import Any, Callable, FunctionType, Mapping, FunctionTypes
from ..typing import NamedTuple, Iterable, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from .fn import fn
    from .. import api as sk

_new = object.__new__


def to_fn(func: Any) -> "fn":
    """
    Convert callable to an :class:`fn` object.

    If func is already an :class:`fn` instance, it is passed as is.
    """
    if isinstance(func, fn):
        return func
    else:
        return fn(func)


def to_function(func: Any, name=None) -> FunctionType:
    """
    Return object as as Python function.

    Non-functions are wrapped into a function definition.
    """

    func = to_callable(func)

    if isinstance(func, FunctionType):
        if name is not None and func.__name__ == "<lambda>":
            func.__name__ = name
        return func

    def f(*args, **kwargs):
        return func(*args, **kwargs)

    if name is not None:
        f.__name__ = name
    else:
        name = getattr(type(func), "__name__", "function")
        f.__name__ = getattr(func, "__name__", name)
    return f


@singledispatch
def _to_callable(func: Any):
    try:
        return func.__sk_callable__
    except AttributeError:
        pass

    if callable(func):
        return func
    else:
        raise TypeError("cannot be interpreted as a callable: %r" % func)


def to_callable(func: Any) -> Callable:
    """
    Convert argument to callable.

    This differs from to_function in which it returns the most efficient
    version of object that has the same callable interface as the argument.

    This *removes* sidekick's function wrappers such as fn and try to convert
    argument to a straightforward function value.

    This defines the following semantics:

    * Sidekick's fn: extract the inner function.
    * None: return the identity function.
    * Mappings: map.__getitem__
    * Functions, methods and other callables: returned as-is.
    """

    try:
        return func.__sk_callable__
    except AttributeError:
        if isinstance(func, FunctionTypes):
            return func
        return _to_callable(func)


to_callable.register = _to_callable.register
to_callable.dispatch = _to_callable.dispatch

to_callable.register(FunctionType, lambda fn: fn)
to_callable.register(type(None), lambda fn: lambda x: x)
to_callable.register(Mapping, lambda dic: dic.__getitem__)


@singledispatch
def arity(func: Callable):
    """
    Return arity of a function.

    Examples:
        >>> from operator import add
        >>> sk.arity(add)
        2
    """

    if hasattr(func, "arity"):
        return func.arity()

    spec = inspect.getfullargspec(func)
    if spec.varargs or spec.varkw or spec.kwonlyargs:
        raise TypeError("cannot curry a variadic function")
    return len(spec.args)


@singledispatch
def signature(func: Callable) -> inspect.Signature:
    """
    Return the signature of a function.
    """

    if hasattr(func, "signature"):
        return func.signature()

    return inspect.Signature.from_callable(func)


@singledispatch
def stub(func: Callable) -> "Stub":
    """
    Return a :class:`Stub` object representing the function signature.
    """

    sig = signature(func)
    return Stub(func.__name__, (sig,))


class Stub(NamedTuple):
    """
    Represent a function declaration Stub.
    """

    name: str
    signatures: Tuple[inspect.Signature]

    def __str__(self):
        return self.render()

    def _stub_declarations(self) -> Iterable[str]:
        name = self.name

        if len(self.signatures) == 0:
            yield f"def {name}(*args, **kwargs) -> Any: ..."
        elif len(self.signatures) == 1:
            yield f"def {name}{self.signatures[0]}: ..."
        else:
            for sep, sig in enumerate(self.signatures):
                prefix = "\n" if sep else ""
                return f"{prefix}@overload\ndef {name}{sig}: ..."

    def _import_declarations(self) -> Iterable[str]:
        raise NotImplementedError

    def required_imports(self) -> set:
        """
        Return set of imported symbols
        """

        return set()

    def render(self, imports=False) -> str:
        """
        Render complete stub file, optionally including imports.
        """

        stubs = "\n".join(self._stub_declarations())
        if imports:
            head = "\n".join(self._import_declarations())
            return f"{head}\n\n{stubs}"
        else:
            return stubs


def quick_fn(func: callable) -> "fn":
    """
    Faster fn constructor.

    This is about twice as fast as the regular fn() constructor. It assumes that
    fn is
    """
    new: fn = _new(fn)
    new._func = func
    new.__dict__ = {}
    return new


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


from .fn import fn
