import inspect
from inspect import Parameter

from ..typing import Tuple, Dict, Any, NamedTuple, TYPE_CHECKING

if TYPE_CHECKING:
    from ..types.result import Result


class Args(NamedTuple):
    """
    Represent arguments for a function call.
    """

    args: tuple
    kwargs: dict


class Signature(inspect.Signature):
    """
    Sidekick-enabled signature class.

    It expands Python's builtin inspect.Signature class with some sidekick
    facilities
    """

    parameters: Dict[str, inspect.Parameter]

    @classmethod
    def from_signature(cls, sig: inspect.Signature):
        """
        Return a sidekick Signature from a inspect.Signature instance.
        """
        return cls(sig.parameters.values(), return_annotation=sig.return_annotation)

    @property
    def restype(self) -> type:
        """
        Normalized return type
        """
        return normalize_type(self.return_annotation)

    def argnames(self, how="short") -> Tuple[str, ...]:
        """
        Tuple with argument names.
        """
        args = list(self.args(how))
        if args and args[-1] == ...:
            args.pop()
        return tuple(self.parameters)[: len(args)]

    def args(self, how="short") -> Tuple[type, ...]:
        """
        Return a tuple with function argument types.
        """

        param_kinds = (Parameter.POSITIONAL_ONLY, Parameter.POSITIONAL_OR_KEYWORD)
        if how not in ("short", "long"):
            raise ValueError(f"invalid method: {how}")

        params = []
        for param in self.parameters.values():
            if param.kind in param_kinds:
                if how == "short" and param.default is not Parameter.empty:
                    break
                params.append(normalize_type(param.annotation))
            elif how == "long" and param.kind == Parameter.VAR_POSITIONAL:
                params.append(normalize_type(param.annotation))
                params.append(...)
                break
            else:
                break
        return tuple(params)

    def keywords(self, how="short") -> Dict[str, type]:
        """
        Return a dictionary with signatures of function keyword parameters.
        """
        keywords = {}
        for k, param in self.parameters.items():
            if param.kind == Parameter.KEYWORD_ONLY:
                keywords[k] = normalize_type(param.annotation)
            elif param.kind == Parameter.POSITIONAL_OR_KEYWORD:
                if how == "long" and param.default != Parameter.empty:
                    keywords[k] = normalize_type(param.annotation)
            elif param.kind == Parameter.VAR_KEYWORD:
                keywords[...] = normalize_type(param.annotation)
        return keywords

    def arity(self, how="short") -> int:
        """
        Return the function arity.
        """
        return len(self.args(how))

    def partial(*args, **kwargs) -> "Signature":
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

    def call(*args, **kwargs) -> "Result":
        """
        Execute function and check if it conforms with both input and output
        signatures.

        Return function output wrapped into a Result instance. Invalid signature
        calls are returned as Err(error message), while exceptions raised by
        function are wrapped as is.

        Examples:
            >>> def add(x: int, y: int) -> int:
            ...     return x + y
            >>> sig.call(add, 1, 2)
            Ok(3)
            >>> sig.call(add, 1, 2.0)
            Err(TypeError('argument at position 1 (x) is a float, expect int'))
        """
        from ..types import Err

        self, func, *args = args
        bound = self.checked_args(*args, **kwargs)
        if not bound:
            return bound.map_error(lambda e: e.args[0])
        bound = bound.value

        try:
            out = func(*bound.args, **bound.kwargs)
        except Exception as ex:
            return Err(ex)

        return self.checked_return(out).map_error(lambda e: e.args[0])

    def checked_return(self, value: Any) -> "Result":
        """
        Check if value is a valid return type.
        """
        from ..types import Ok, Err

        try:
            typechecked(value, self.restype)
        except TypeError as exc:
            return Err(TypeError(f"invalid return type: {exc}"))
        return Ok(value)

    def checked_args(*args, **kwargs) -> "Result":
        """
        Check if arguments conform to signature.

        Raises a TypeError if not.
        """
        from ..types import Err, Ok

        self, *args = args
        try:
            return Ok(self.bind(*args, **kwargs))
        except TypeError as ex:
            return Err(ex)


def typechecked(value, cls):
    """
    Raise TypeError if value does not correspond to class.
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
