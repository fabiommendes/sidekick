import os
from inspect import Parameter
from itertools import count
from typing import NamedTuple, List, Optional, Dict, Callable, Any

from ...functions import Signature, to_callable, signature

WRAPPED_FUNCTION_CODE = """
def {name}{sig}:
    return __display__(__call__({args}))
"""


class DecomposedParams(NamedTuple):
    pos_only: List[Parameter]
    required: List[Parameter]
    optional: List[Parameter]
    varargs: Optional[Parameter]
    kw_required: Dict[str, Parameter]
    kw_optional: Dict[str, Parameter]
    varkwargs: Optional[Parameter]

    def signature(self, return_annotation=None) -> Signature:
        """
        Create a signature object from decomposition.
        """
        args = [*self.pos_only, *self.required, *self.optional]
        if self.varargs:
            args.append(self.varargs)
        args.extend(self.kw_required.values())
        args.extend(self.kw_optional.values())
        if self.varkwargs:
            args.append(self.varkwargs)

        return Signature(args, return_annotation=return_annotation)

    def replace(self, **kwargs) -> "DecomposedParams":
        """
        Replace attribute from decomposed params.
        """
        out = DecomposedParams(
            kwargs.pop("pos_only", self.pos_only),
            kwargs.pop("required", self.required),
            kwargs.pop("optional", self.optional),
            kwargs.pop("varargs", self.varargs),
            kwargs.pop("kw_required", self.kw_required),
            kwargs.pop("kw_optional", self.kw_optional),
            kwargs.pop("varkwargs", self.varkwargs),
        )
        if kwargs:
            raise TypeError(f"invalid argument: {kwargs.popitem()[0]}")
        return out


def decompose(self):
    """
    Return a namedtuple with the parts of function signature.
    """

    params: List[Parameter] = list(self.parameters.values())
    pos_only = []
    required = []
    optional = []
    varargs = None
    kw_required = {}
    kw_optional = {}
    varkwargs = None

    for p in params:
        if p.kind == p.POSITIONAL_ONLY:
            pos_only.append(p)
        elif p.kind == p.POSITIONAL_OR_KEYWORD:
            if p.default is p.empty:
                required.append(p)
            else:
                optional.append(p)
        elif p.kind == p.VAR_POSITIONAL:
            if varargs is not None:
                raise ValueError(f"duplicated varargs: {varargs}, {p}")
            varargs = p
        elif p.kind == p.VAR_KEYWORD:
            if varkwargs is not None:
                raise ValueError(f"duplicated varkwargs: {varkwargs}, {p}")
            varkwargs = p
        elif p.kind == p.KEYWORD_ONLY:
            if p.default is p.empty:
                kw_required[p.name] = p
            else:
                kw_optional[p.name] = p
        else:
            raise ValueError

    return DecomposedParams(
        pos_only=pos_only,
        required=required,
        optional=optional,
        varargs=varargs,
        kw_required=kw_required,
        kw_optional=kw_optional,
        varkwargs=varkwargs,
    )


class _Var(str):
    def __repr__(self):
        return self


def wrap_function(
    fn: Callable,
    parse_value: Callable[[str], Any] = None,
    display: Callable[[Any], str] = None,
) -> Callable:
    """
    Wrap callable in function type.
    """
    name = fn.__name__
    parse_value = parse_value or (lambda x: x)
    display = display or (lambda x: x)

    # We want to be able to call all arguments by name. This removes
    # positional-only arguments from signature
    sig = signature(fn)
    dec = decompose(sig)
    required = [p.replace(kind=p.POSITIONAL_OR_KEYWORD) for p in dec[0]]
    required.extend(dec[1])
    dec = dec.replace(pos_only=[], required=required)
    sig = dec.signature(sig.return_annotation)

    # We create fake vars for default values of parameters and add the
    # real values to a namespace dictionary that will be used to construct
    # function using eval
    ns = {
        "__call__": to_callable(fn),
        "__parse__": parse_value,
        "__display__": display,
    }
    params = []
    args = []
    tnames = iter(f"T{i}" for i in count())

    for name, p in sig.parameters.items():
        src = name
        T = next(tnames)
        ns[T] = p.annotation
        if p.default is not p.empty:
            ns[name] = p.default
            src = f"{name}=__parse__({name})"
            p = p.replace(default=_Var(name), annotation=_Var(T))
        elif p.kind == p.POSITIONAL_OR_KEYWORD and p.annotation is p.empty:
            src = f"__parse__({p.name})"

        params.append(p)
        args.append(src)

    sig = Signature(params, return_annotation=sig.return_annotation)

    # Now we compile the source code to create function
    src = WRAPPED_FUNCTION_CODE.format(name=name, sig=sig, args=", ".join(args))
    if os.environ.get("DEBUG", "false").lower() == "true":
        print(src)
    exec(src, ns)
    func = ns[name]
    assert callable(func), {k: type(v) for k, v in ns.items()}
    return func
