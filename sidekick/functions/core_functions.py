import inspect
from functools import singledispatch

from sidekick.typing import Callable, NamedTuple, Iterable, Tuple


@singledispatch
def arity(func: Callable):
    """
    Return arity of a function.

    Examples:
        >>> arity(lambda x, y: x + y)
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
