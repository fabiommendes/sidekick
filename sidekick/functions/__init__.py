from . import core_functions as _core
from .core_functions import to_fn, to_function, to_callable, quick_fn
from .fn import fn
from .._modules import set_module_class, LazyPackage

from .lib_partial_application import partial, rpartial, curry
from .lib_composition import (
    compose,
    pipe,
    pipeline,
    thread,
    rthread,
    thread_if,
    rthread_if,
    juxt,
)
from .lib_combinators import identity, ridentity, always, rec, power, trampoline
from .lib_runtime import once, thunk, call_after, call_at_most, throttle, background

set_module_class(__name__, LazyPackage)

__all__ = [
    # Base
    "fn",
    "quick_fn",
    # Introspection
    "Stub",
    "arity",
    "signature",
    "stub",
    # Transforms
    "to_function",
    "to_callable",
    "to_fn",
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

Stub = _core.Stub
arity = fn(_core.arity)
signature = fn(_core.signature)
stub = fn(_core.stub)
