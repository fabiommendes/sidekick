from .. import _fn_introspection as _introspection
from .._fn import fn
from .._modules import module_class, LazyPackage
from ..typing import TYPE_CHECKING

# This modules are lazy loaded to improve efficiency
if TYPE_CHECKING:
    from .partial_application import partial, rpartial, curry
    from .composition import compose, pipe, pipeline, thread, rthread
    from .combinators import identity, ridentity, always, rec, power

module_class(__name__, LazyPackage)

__all__ = [
    # Base
    "fn",
    # Introspection
    "Stub",
    "arity",
    "signature",
    "stub",
    # Partial application
    "curry",
    "partial",
    "rpartial",
    # Composition
    "compose",
    "pipe",
    "pipeline",
    "thread",
    "rthread",
    # Combinators
    "identity",
    "ridentity",
    "always",
    "rec",
    "power",
]

Stub = _introspection.Stub
arity = fn(_introspection.arity)
signature = fn(_introspection.signature)
stub = fn(_introspection.stub)
