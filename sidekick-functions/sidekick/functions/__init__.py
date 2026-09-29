from sidekick.core import (
    to_fn,
    to_function,
    to_callable,
    quick_fn,
    signature,
    arity,
    stub,
    fn,
    wrap_fn_functions as _wrap_fn_functions,
)
from .arguments import (
    flip,
    select_args,
    keep_args,
    reverse_args,
    skip_args,
    unsplice,
    variadic,
    default_args,
)
from .creation import (
    identity,
    ridentity,
    always,
    rec,
    power,
    trampoline,
    value,
    call,
    do,
)
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
from .partial import partial, rpartial, curry, method
from .runtime import (
    once,
    thunk,
    call_after,
    call_at_most,
    throttle,
    background,
    error,
    retry,
    catch,
    catching,
)
from .signature import Signature, BoundArguments, Parameter
from .stub import Stub

__all__ = [
    # Base
    "_",
    "fn",
    "quick_fn",
    "X",
    "Y",
    "F",
    "M",
    "placeholder",
    "Placeholder",
    "Signature",
    "BoundArguments",
    "Parameter",
    "Stub",
    # Introspection
    "Stub",
    "arity",
    "signature",
    "stub",
    # Transforms
    "to_function",
    "to_callable",
    "to_fn",
    # Functional interfaces,
    "semigroup",
    "monoid",
    "group",
    "apply",
    "apply_flat",
    "mtimes",
    "mconcat",
    # Partial application
    "curry",
    "partial",
    "rpartial",
    "method",
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
    "call",
    "value",
    "do",
    # Runtime control
    "once",
    "thunk",
    "call_after",
    "call_at_most",
    "throttle",
    "background",
    "error",
    "retry",
    "catching",
    "catch",
    # Arguments
    "flip",
    "select_args",
    "keep_args",
    "reverse_args",
    "skip_args",
    "unsplice",
    "variadic",
    "default_args",
]
__version__ = "0.1.0"
_wrap_fn_functions(globals(), exclude={"fn", "placeholder", "_", "X", "Y", "M", "F"})
# TODO: _instances.register_all()
