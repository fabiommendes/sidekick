from __future__ import annotations

import logging
import sys
import warnings
from types import FunctionType
from typing import TYPE_CHECKING
from typing import Callable as Fn
from typing import Generic, ParamSpec, Type, TypeVar, Union

if sys.version_info >= (3, 11):
    from typing import TypeVarTuple, assert_never
else:
    from typing_extensions import TypeVarTuple, assert_never  # noqa: F401

if TYPE_CHECKING:
    from .maybe import Just, Maybe, Nothing
    from .result import Err, Ok, Result

log = logging.getLogger("sidekick")
a = TypeVar("a")
b = TypeVar("b")
r = TypeVar("r")
err = TypeVar("err")
err_ = TypeVar("err_")
err_co = TypeVar("err_co", covariant=True)
args_t = TypeVarTuple("args_t")
BinOp = Fn[[a, a], a]
res = TypeVar("res", bound=Union["Maybe", "Result"])
P = ParamSpec("P")
Raisabled = Type[Exception] | Exception
NOT_GIVEN = object()


class Constant:
    @property
    def CTE(self: a) -> a:
        return self

    def __new__(cls: Type[a]) -> a:
        try:
            return cls._instance  # type: ignore
        except AttributeError:
            cls._instance = object.__new__(cls)
            return cls._instance  # type: ignore

    def __repr__(self):
        return type(self).__name__.lstrip("_").removesuffix("T")


def optimized(base: type | None = None) -> Fn[[type], type]:
    '''
    Read all methods of base class and try to create optimized
    methods for some case.

    Fill the locals() dictionary with the optimized version of the methods.

    Args:
        base: Abstract base class of a union.
        locals: The locals() dictionary for the target class.

    Returns:
        A mapping from method names to the optimized version of
        methods.

    Example:

        Create the base class and some implementations

        >>> class List:
        ...     """List = Nil | Node(a, List)"""
        ...
        ...     def map(self, func):
        ...         match self:
        ...             case Nil():
        ...                 return Nil
        ...             case Node(head, tail):
        ...                 return Node(func(head), tail.map(func))
        ...
        ...      # ... and other implementations

        Now we create each case and call optimized(base, locals()) in the
        end of the class body to fill in with the optimized methods.

        >>> @optimized()
        ... class Nil(Constant, List):
        ...     """An empty list"""
        ...
        ...     # This will build the optimized versions of each method
        ...     # The optimizer targets functions defined as match/case expressions
        ...     # Like the implementation of map() above.
        ...
        >>> @optimized()
        ... @dataclass(frozen=True)
        ... class Node(List):
        ...     """A node in a linked list"""
    '''

    def decorator(typ: type) -> type:
        if base is None:
            if getattr(typ, "__sk_is)_unit_instance__", False):
                typ = type(typ)
            bases = typ.__bases__
        else:
            bases = (base,)

        for base_cls in bases:
            _optimize(base_cls, typ)
        return typ

    return decorator


def _optimize(base: type, case_type: type) -> None:
    # Implements the @optimized(...) decorator
    assert isinstance(case_type, type)
    assert isinstance(base, type)

    base_protected_prefix = f"_{base.__name__}__"
    try:
        case_name = case_type.__name__
        for_case_attr = f"for_{case_name}"
    except KeyError:
        warnings.warn(
            "could not determine case name for specialization. Is __qualname__ undefined?"
        )
        return

    methods: dict[str, FunctionType] = {}
    for attr in dir(base):
        if attr.startswith("_") and not attr.startswith("__"):
            continue
        if attr in case_type.__dict__:
            continue
        if attr.startswith(base_protected_prefix):
            continue

        obj = getattr(base, attr)
        if not isinstance(obj, FunctionType):
            continue
        if getattr(obj, "specialize", True) is False:
            continue
        if (impl := getattr(obj, for_case_attr, None)) is not None:
            setattr(case_type, attr, impl)
            continue

        methods[attr] = obj

    # TODO: in thg future, cache optimized trees in a separate module and prevent
    # importing the ast_optimizer module.
    from .ast_optimizer import specialize_method

    n_methods = 0
    for attr, method in methods.items():
        specialized = specialize_method(method, case_type)
        if specialized is not None:
            setattr(case_type, attr, method)
            n_methods += 1

    log.info(f"optimized {case_name}: found {n_methods} methods")


#
# Conversions
#
def to_callable(obj):
    """
    Extract callable using obj.__sk_callable__() protocol.
    """
    try:
        get_callable = obj.__sk_callable__
    except AttributeError:
        if callable(obj):
            return obj
        raise TypeError(f"not callable: f{type(obj).__name__}")
    else:
        return get_callable()


def to_raisable(obj) -> Raisabled:
    """
    Convert argument to something that can be raised.
    """
    if isinstance(obj, Exception):
        return obj
    elif isinstance(obj, type) and issubclass(obj, Exception):
        return obj
    return ValueError(obj)


#
# Factory functions
#
def result_operator(op: BinOp[a]):
    """
    Factory function that implements binary operators for the Result class.
    """

    def result_op(self, other):
        if isinstance(other, Result):
            match (self, other):
                case (Ok(x), Ok(y)):
                    return Ok(op(x, y))
                case (Err(_) as err, _) | (_, Err(_) as err):
                    return err
        return NotImplemented

    def ok_op(self, other):
        if type(other) == Ok:
            return op(self.value, other.value)
        elif type(other) == Err:
            return other
        return NotImplemented

    def err_op(self, other):
        if isinstance(other, Result):
            return self
        return NotImplemented

    result_op.for_Ok = ok_op  # type: ignore
    result_op.for_Err = err_op  # type: ignore
    return result_op


def maybe_operator(op: BinOp[a]):
    def maybe_op(self, other):
        match self:
            case Just(x):
                match other:
                    case Maybe.Nothing:
                        return Nothing
                    case Just(y) | y:
                        return Just(op(x, y))
            case _:
                return Nothing

    def just_op(self: Just, other):
        match other:
            case Maybe.Nothing:
                return Nothing
            case Just(y) | y:
                return Just(op(self.value, y))

    maybe_op.for_Just = just_op  # type: ignore
    maybe_op.for_Nothing = lambda _, __: Nothing  # type: ignore
    return maybe_op


#
# Attribute descriptors
#
class BoundAttrGetter(Generic[res]):
    """
    Implements the attr() method.
    """

    __slots__ = ("_instance", "_wrapper")
    _instance: res
    _wrapper: Fn[[a | None], res]

    def __init__(self, instance: res, wrapper: Fn[[a | None], res]):
        self._instance = instance
        self._wrapper = wrapper

    def __getattr__(self, attr):
        instance = self._instance
        if instance.is_success:
            # We let AttributeErrors pass. These should be easily
            # flagged by a static analyzer and are often caused by typos
            # in the name of variables.
            #
            # The motivation for this behavior is to wrap legitimate exceptions
            # triggered by some condition in the state of the program, but
            # fail fast with exceptions most likely caused by programmer
            # error.
            value = getattr(instance.value, attr)
            return self._wrapper(value)
        return instance

    __call__ = __getattr__


class BoundMethodGetter(BoundAttrGetter[res]):
    """
    Implements the method() method.
    """

    __slots__ = ()

    def __call__(self, name, /, *args, **kwargs):
        return self.__getattr__(name)(*args, **kwargs)
