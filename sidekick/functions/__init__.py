from .. import _fn_introspection as _introspection
from .._fn import fn
from .._modules import set_module_class, LazyPackage

from .partial_application import partial, rpartial, curry
from .composition import (
    compose,
    pipe,
    pipeline,
    thread,
    rthread,
    thread_if,
    rthread_if,
    juxt,
)
from .combinators import identity, ridentity, always, rec, power, trampoline
from .runtime import once, thunk, call_after, call_at_most, throttle, background

set_module_class(__name__, LazyPackage)

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
    "thread_if",
    "rthread_if",
    "juxt",
    # Combinators
    "identity",
    "ridentity",
    "always",
    "rec",
    "power",
    "trampoline",
    # Runtime control
    "once",
    "thunk",
    "call_after",
    "call_at_most",
    "throttle",
    "background",
]

Stub = _introspection.Stub
arity = fn(_introspection.arity)
signature = fn(_introspection.signature)
stub = fn(_introspection.stub)
