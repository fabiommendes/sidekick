from . import core_functions as _core
from . import fn_instances as _instances
from . import fn_mixins as _mixins
from .core_functions import (
    to_fn,
    to_function,
    to_callable,
    quick_fn,
    signature,
    arity,
    declaration as stub,
)
from .fn import fn, wrap_fn_functions as _wrap_fn_functions
from .fn_interfaces import semigroup, monoid, group, apply, apply_flat, mtimes, mconcat
from .fn_placeholders import X, Y, F, placeholder, _, Placeholder
from .lib_arguments import (
    flip,
    select_args,
    keep_args,
    reverse_args,
    skip_args,
    splice_args,
    variadic_args,
    set_null,
)
from .lib_combinators import (
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
from .lib_partial_application import partial, rpartial, curry, method
from .lib_runtime import (
    once,
    thunk,
    call_after,
    call_at_most,
    throttle,
    background,
    error,
    raising,
    retry,
    catch,
)
from .signature import Signature
from .stub import Stub
from .._modules import set_module_class, LazyPackage

set_module_class(__name__, LazyPackage)
__all__ = [
    # Base
    "_",
    "fn",
    "quick_fn",
    "X",
    "Y",
    "F",
    "placeholder",
    "Placeholder",
    "Signature",
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
    "raising",
    "retry",
    "catch",
    # Arguments
    "flip",
    "select_args",
    "keep_args",
    "reverse_args",
    "skip_args",
    "splice_args",
    "variadic_args",
    "set_null",
]

_wrap_fn_functions(globals(), exclude={"fn", "placeholder", "_", "X", "Y"})
_instances.register_all()
_mixins.patch_fn()
