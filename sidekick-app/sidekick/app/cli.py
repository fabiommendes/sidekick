import sys
import os
from types import ModuleType
from typing import IO, Any, Callable, Dict, List, Optional, Tuple, Union, TypedDict
from functools import wraps

import typer
import click
from typer.models import ParameterInfo

from sidekick.proxy import import_later, touch
from sidekick.functions import Signature, Parameter

from .config import Parser, Display, parse_input, display_result

__all__ = ["Parser", "Display", "run", "parse_input", "display_result"]

#
# Constants
#
FUNCTION_SRC = """
def {name}({argdefs}) -> {restype}:
    {body}
    __display__(__call__({argvalues}), __stdout__)
"""


class WrapperOpts(TypedDict):
    parse: Parser
    display: Display
    stdout: IO


class BuiltinWrapError(NotImplementedError):
    """
    Raised when trying to wrap a builtin function.
    """


def run(
    fn_or_mod: Union[Callable, ModuleType],
    parse: Optional[Parser] = None,
    display: Optional[Display] = None,
    command: str = None,
    stdout: IO = sys.stdout,
    runner: Callable[[typer.Typer], Any] = lambda app: app(),
):
    """
    Create a CLI app using function.

    Args:
        fn:
            Input function.
        parse:
            Convert string values of non-annotated arguments using this
            function.
        display:
            Print the result value of function.
        command:
            Optional command used to register function.
        builder:
            A function responsible for running the Typer app.
    """
    opts: WrapperOpts = {
        "parse": parse or parse_input,
        "display": display or display_result,
        "stdout": stdout,
    }

    if callable(fn_or_mod):
        fn = fn_or_mod
        wrapped = _wrap_function(fn, **opts)
        app = typer.Typer(name=getattr(fn_or_mod, "__name__", command or "func"))
        app.command(command)(wrapped)
        return runner(app)
    else:
        mod = fn_or_mod
        app = _wrap_module(mod, **opts)
        return runner(app)


def main(runner=run):
    """
    Called when executed as "python -m sidekick.app.cli ...".
    """
    try:
        target = sys.argv[1]
    except IndexError:
        msg = [
            click.style("ERROR:", fg="red", bold=True),
            click.style("must provide a Python module or function.", fg="green"),
        ]
        click.echo(" ".join(msg), err=True)
        exit()

    obj = touch(import_later(target))
    if callable(obj):
        command = target

        def app_runner(app):
            app.command("_")(lambda: None)
            return app()

    else:
        command = None

        def app_runner(app):
            del sys.argv[1]
            return app()

    return runner(obj, command=command, runner=app_runner)


#
# Auxiliary functions
#
def _wrap_function(
    fn: Callable, parse: Parser, display: Display, stdout: IO
) -> Callable:
    if not callable(fn):
        raise TypeError(f"trying to wrap a non-callable: {fn!r}")
    try:
        sig = Signature.from_callable(fn)
    except ValueError:
        raise NotImplementedError(f"could not wrap: {fn}")

    func_name = getattr(fn, "__name__", "func")
    env = {
        "wraps": wraps,
        "__call__": fn,
        "__display__": display,
        "__parse__": parse,
        "__restype__": sig.return_annotation,
        "__stdout__": stdout,
    }
    body: List[str] = []
    argdefs: List[str] = []
    args: List[str] = []
    kwargs: List[str] = []

    for arg_name, param in sig.parameters.items():
        default_var = f"{arg_name}_default"

        # Parameter info
        info, cmds = _argument_info_and_commands(arg_name, param)
        body.extend(cmds)
        env[default_var] = info

        # Annotation
        if param.annotation == param.empty:
            body.append(f"{arg_name} = __parse__({arg_name})")
            annotated = f"{arg_name}"
        else:
            annotation = _repr_type_annotation(env, arg_name, param.annotation)
            annotated = f"{arg_name}: {annotation}"
        argdefs.append(f"{annotated}={default_var}")

        # Function call and definition
        if param.kind == param.POSITIONAL_ONLY:
            args.append(arg_name)
        else:
            kwargs.append(f"{arg_name}={arg_name}")

    # Create source
    src = FUNCTION_SRC.format(
        name=func_name,
        body="\n    ".join(body),
        argdefs=", ".join(argdefs),
        argvalues=", ".join(args + kwargs),
        restype=_repr_type_annotation(env, "restype", sig.return_annotation),
    )

    if os.environ.get("SK_DEBUG", "false").lower() == "true":
        data = "\n".join("    " + ln for ln in src.splitlines())
        click.echo(click.style("-" * 40, fg="yellow"))
        click.echo(click.style("WRAPPED FUNCTION SOURCE CODE", bold=True, fg="yellow"))
        click.echo(click.style(data + "\n", fg="yellow"))
        click.echo(click.style("-" * 40 + "\n", fg="yellow"))

    exec(src, env)
    func = env[func_name]
    func.__doc__ = getattr(fn, "__doc__", None)
    return func


def _argument_info_and_commands(
    name: str, param: Parameter
) -> Tuple[ParameterInfo, List[str]]:
    cmds = []
    is_positional = param.kind in (param.POSITIONAL_ONLY, param.POSITIONAL_OR_KEYWORD)

    # Argument type

    if param.default != param.empty:
        info = typer.Option(default=param.default)
    elif is_positional:
        info = typer.Argument(None)
        cmds.append(f"if {name} is None:")
        cmds.append(f"    {name} = __parse__(input('{name}: '))")
    else:
        info = typer.Option(None)
        cmds.append(f"if {name} is None:")
        cmds.append(f"    {name} = __parse__(input('{name}: '))")

    return info, cmds


def _wrap_module(mod: ModuleType, **kwargs) -> typer.Typer:
    app = typer.Typer()
    for name, fn in _extract_functions(mod).items():
        try:
            wrapped = _wrap_function(fn, **kwargs)
        except NotImplementedError:
            continue
        else:
            app.command(name)(wrapped)

    return app


def _extract_functions(mod: ModuleType) -> Dict[str, Callable]:
    ns = {}
    names = getattr(mod, "__all__", dir(mod))
    for var in names:
        fn = getattr(mod, var, None)
        if callable(fn):
            ns[var] = fn
    return ns


def _repr_type_annotation(env: Dict[str, Any], name: str, annotation: Any):
    if annotation in {int, float, bool, str, list, dict}:
        return annotation.__name__
    if annotation is Signature.empty:
        env["Any"] = Any
        return "Any"
    key = f"{name}_T"
    env[key] = annotation
    return key


if __name__ == "__main__":
    main()
