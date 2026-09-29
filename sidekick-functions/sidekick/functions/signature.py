from __future__ import annotations

import inspect
from typing import Any, NamedTuple, Literal, TYPE_CHECKING

from sidekick.results import Ok, Err

from .utils import a, b, r, Fn


if TYPE_CHECKING:
    from sidekick.results import Result


ArityT = Literal["short", "long"]
_empty = inspect.Parameter.empty
_param_T = type(inspect.Parameter.POSITIONAL_ONLY)


class Args(NamedTuple):
    """
    Represent arguments for a function call.
    """

    args: tuple[Any, ...]
    kwargs: dict[str, Any]


class Parameter(inspect.Parameter):
    """
    Represents a parameter in a function signature.

    Has the following public attributes:

    * name : str
        The name of the parameter as a string.
    * default : object
        The default value for the parameter if specified.  If the
        parameter has no default value, this attribute is set to
        `Parameter.empty`.
    * annotation
        The annotation for the parameter if specified.  If the
        parameter has no annotation, this attribute is set to
        `Parameter.empty`.
    * kind : str
        Describes how argument values are bound to the parameter.
        Possible values: `Parameter.POSITIONAL_ONLY`,
        `Parameter.POSITIONAL_OR_KEYWORD`, `Parameter.VAR_POSITIONAL`,
        `Parameter.KEYWORD_ONLY`, `Parameter.VAR_KEYWORD`.

    This class extends inspect.Parameter with the following optional attributes:

    * description : str
        A long description, usually extracted from the docstring.
    * label : str
        A human-friendly name for the parameter.
    """

    annotation: str | None
    description: str | None

    def __init__(
        self,
        name: str,
        kind: _param_T,
        *,
        default: Any = _empty,
        annotation: Any = _empty,
        description: str | None = None,
        label: str | None = None,
    ) -> None:
        super().__init__(
            name,
            kind,
            default=default,
            label=label,
        )
        self.annotation = annotation
        self.description = description


class BoundArguments(inspect.BoundArguments):
    """
    Result of `Signature.bind` call.  Holds the mapping of arguments
    to the function's parameters.

    Has the following public attributes:

    * arguments : dict
        An ordered mutable mapping of parameters' names to arguments' values.
        Does not contain arguments' default values.
    * signature : Signature
        The Signature object that created this instance.
    * args : tuple
        Tuple of positional arguments values.
    * kwargs : dict
        Dict of keyword arguments values.
    """

    def call(self, callable: Fn):
        """
        Call object with the bound arguments.
        """
        return callable(*self.args, **self.kwargs)


class Signature(inspect.Signature):
    """
    Sidekick-enabled signature class.

    It expands Python's builtin inspect.Signature class with some sidekick
    facilities
    """

    parameters: dict[str, Parameter]

    @classmethod
    def from_signature(cls, sig: inspect.Signature) -> Signature:
        """
        Return a sidekick Signature from a inspect.Signature instance.
        """
        params = list(sig.parameters.values())
        return cls(params, return_annotation=sig.return_annotation)

    @classmethod
    def from_callable(cls, obj: Fn, **kwargs) -> Signature:
        return super().from_callable(obj, **kwargs)

    @property
    def restype(self) -> type:
        """
        Normalized return type
        """
        return normalize_type(self.return_annotation)

    def update_from_docstring(
        self, obj: Any, format: Literal["google"] = "google", lenient: bool = False
    ):
        """
        Update signature with docstring information.

        Args:
            obj:
                A string or object with docstring annotation.
            format:
                The docstring format.
            lenient:
                If True, inconsistent parameters in docstring are simply ignored.
        """
        from .docstrings import parse_google_docstring

        if not isinstance(obj, str):
            try:
                obj = obj.__doc__
            except AttributeError:
                typ = type(obj).__name__
                raise TypeError(f"{typ} object does not have a __doc__ attribute.")
            else:
                if obj is None:
                    return

        if format == "google":
            docstring = parse_google_docstring(obj)
        else:
            raise ValueError("only 'google' format docstrings are supported")

        if diff := set(docstring) - self.parameters:
            param = next(iter(diff))
            raise ValueError(f"docstring parameter '{param}' not present in signature.")

        for name, arg in docstring.args.items():
            self.parameters[name].description = arg.description

    def argnames(self, arity: ArityT = "short") -> tuple[str, ...]:
        """
        Tuple with argument names.
        """
        args = self.argtypes(arity)
        if args and args[-1] == ...:
            args = args[:-1]
        return tuple(self.parameters)[: len(args)]

    def argtypes(self, arity: ArityT = "short") -> tuple[type, ...]:
        """
        Return a tuple with function argument types.
        """

        param_kinds = (Parameter.POSITIONAL_ONLY, Parameter.POSITIONAL_OR_KEYWORD)
        if arity not in ("short", "long"):
            raise ValueError(f"invalid method: {arity}")

        params = []
        for param in self.parameters.values():
            if param.kind in param_kinds:
                if arity == "short" and param.default is not Parameter.empty:
                    break
                params.append(normalize_type(param.annotation))
            elif arity == "long" and param.kind == Parameter.VAR_POSITIONAL:
                params.append(normalize_type(param.annotation))
                params.append(...)
                break
            else:
                break
        return tuple(params)

    def keywords(self, arity: ArityT = "short") -> dict[str, type]:
        """
        Return a dictionary with signatures of function keyword parameters.
        """
        keywords = {}
        for k, param in self.parameters.items():
            if param.kind == Parameter.KEYWORD_ONLY:
                keywords[k] = normalize_type(param.annotation)
            elif param.kind == Parameter.POSITIONAL_OR_KEYWORD:
                if arity == "long" and param.default != Parameter.empty:
                    keywords[k] = normalize_type(param.annotation)
            elif param.kind == Parameter.VAR_KEYWORD:
                keywords[...] = normalize_type(param.annotation)
        return keywords

    def arity(self, arity: ArityT = "short") -> int:
        """
        Return the function arity.

        A "short" arity (default) represents the minimum number of required
        positional parameters necessary to call the function.

        The "long" arity represents the maximum number of positional
        parameters, including parameters with default values.

        >>> def incr(x, by=1):
        ...     return x + by
        >>> sig = Signature.from_callable(incr)
        >>> sig.arity("short")  # default!
        1
        >>> sig.arity("long")
        2
        """
        return len(self.argtypes(arity))

    def partial(*args, **kwargs) -> Signature:
        """
        Partially apply arguments and return the corresponding signature object.

        This method emulates auto-currying.
        """
        self, *args = args
        self: Signature

        partial = self.bind_partial(*args, **kwargs)
        pairs = list(self.parameters.items())
        del pairs[: len(partial.args)]

        params = [p for k, p in pairs if k not in partial.kwargs]
        return Signature(params, return_annotation=self.return_annotation)

    def checked_call(
        self, func: Fn[..., r], /, *args, **kwargs
    ) -> Result[Exception, r]:
        """
        Execute function and check if it conforms with both input and output
        signatures.

        Return function output wrapped into a Result instance. Invalid signature
        calls are returned as Err(error message), while exceptions raised by
        function are wrapped as is.

        Examples:
            >>> def add(x: int, y: int) -> int:
            ...     return x + y
            >>> sig = sk.signature(add)
            >>> sig.call(add, 1, 2)
            Ok(3)
            >>> sig.call(add, 1, 2j)
            Err('invalid argument (y): complex, expect int')
        """
        bound = self.checked_args(*args, **kwargs)
        if isinstance(bound, Ok):
            bound = bound.value
        else:
            return bound.map_error(lambda e: e.args[0])

        try:
            out = func(*bound.args, **bound.kwargs)
        except Exception as ex:
            return Err(ex)

        return self.check_return(out).map_error(lambda e: e.args[0])

    def check_return(self, value: a) -> Result[TypeError, a]:
        """
        Check if value is a valid return type.
        """
        try:
            typechecked(value, self.restype)
        except TypeError as exc:
            return Err(TypeError(f"invalid return type: {exc}"))
        return Ok(value)

    def checked_args(
        self, /, *args, **kwargs
    ) -> Result[TypeError, inspect.BoundArguments]:
        """
        Check if arguments conform to signature.

        Return an Err(TypeError) if not.
        """
        try:
            bind: inspect.BoundArguments = self.bind(*args, **kwargs)
            for name, sig in self.parameters.items():
                value = bind.arguments[name]
                try:
                    typechecked(value, normalize_type(sig.annotation))
                except TypeError as e:
                    return Err(TypeError(f"invalid argument ({name}): {e}"))
            return Ok(bind)
        except TypeError as ex:
            return Err(ex)


def typechecked(value: Any, cls: type):
    """
    Raise TypeError if value does not correspond to class.

    Args:
        value:
            Any python value.
        cls:
            Class for instance check.

    Return:
        Nothing
    """
    if cls is Any:
        return

    try:
        is_instance = isinstance(value, cls)
    except TypeError:
        raise RuntimeError

    if not is_instance:
        kind = type(value).__name__
        raise TypeError(f"{kind}, expect {cls.__name__}")


def normalize_type(typ) -> type:
    if typ is Signature.empty:
        return Any
    return typ
