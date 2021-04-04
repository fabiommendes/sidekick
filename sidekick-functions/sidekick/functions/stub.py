from typing import Tuple, Iterable

from .signature import Signature


class Stub:
    """
    Represent a function declaration.

    It includes the function name and can contain multiple overloaded signatures.

    It is basically an aggregation of function names and their respective
    signatures.
    """

    name: str
    signatures: Tuple[Signature]

    def __init__(self, name, signatures):
        self.name = name
        self.signatures = tuple(to_signature(sig) for sig in signatures)

    def __str__(self):
        return self.render()

    def __repr__(self):
        name = type(self).__name__
        sigs = ", ".join(map(repr, self.signatures))
        return f"{name}({self.name!r}, [{sigs}])"

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

    def bind(self, *args, **kwargs):
        """
        Bind function call to first viable signature.
        """
        return self._bind(False, *args, **kwargs)

    def bind_partial(self, *args, **kwargs):
        """
        Partially binds function call to first viable signature.
        """
        return self._bind(True, *args, **kwargs)

    def _bind(*args, **kwargs):
        self, partial, *args = args
        n_sigs = len(self.signatures)
        for n, sig in enumerate(self.signatures, 1):
            try:
                if partial:
                    return sig.bind_partial(*args, **kwargs)
                else:
                    return sig.bind(*args, **kwargs)
            except TypeError:
                if n == n_sigs:
                    raise

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


def to_signature(x) -> "Signature":
    """
    Convert object to sidekick signature.
    """
    if isinstance(x, Signature):
        return x
    else:
        return Signature.from_signature(x)
