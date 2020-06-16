from .. import _fn_introspection as _introspection
from .._fn import fn

__all__ = [
    # Base
    "fn",
    # Introspection
    "Stub",
    "arity",
    "signature",
    "stub",
]

Stub = _introspection.Stub
arity = fn(_introspection.arity)
signature = fn(_introspection.signature)
stub = fn(_introspection.stub)
