import ast
import copy
import inspect
import sys
from textwrap import dedent
from types import FunctionType
from typing import Any, cast


def specialize_method(func: FunctionType, case_type: type) -> FunctionType | None:
    """
    Given a method of the form:

    >>> def method(self, *args):
    ...     ... # preparation
    ...
    ...     match self:
    ...         case Case1(arg1):
    ...             impl_case1
    ...         case Case2(arg2):
    ...             impl_case2
    ...         # ...
    ...
    ...     ... # finish

    Extract the desired case and reimplement a method like


    >>> def method(self, *args):
    ...     ... # preparation
    ...
    ...     v1 = self.v1  # from case Case(v1, v2):
    ...     v2 = self.v2
    ...     impl_case
    ...
    ...     ... # finish

    Args:
        func (FunctionType):
            The generic function
        case (str):
            A string with the case name.

    Returns:
        FunctionType | None:
            The specialized function, if specialization succeed, or None if a suitable specialization
            could not be found.
    """
    assert isinstance(case_type, type), case_type

    source_code = dedent(inspect.getsource(func))
    func_def = cast(ast.FunctionDef, ast.parse(source_code).body[0])
    func_def = copy.copy(func_def)
    try:
        self_name = ast.unparse((func_def.args.posonlyargs + func_def.args.args)[0])
    except IndexError:
        return None

    new_body = []
    for node in func_def.body:
        new_body.extend(specialize_stmt(node, self_name, case_type))
    if new_body == func_def.body:
        return None

    func_def.body[:] = new_body
    source = ast.unparse(func_def)
    mod = sys.modules[case_type.__module__]
    namespace: dict[str, Any] = {}
    exec(source, mod.__dict__, namespace)
    return namespace[func.__name__]


def specialize_stmt(node: ast.stmt, self_name, case_type: type) -> list[ast.stmt]:
    """
    Specialize statement to case.

    Currently it only modifies ast.Match nodes.

    Return a list of transformed statements.
    """

    case_name = case_type.__name__
    match_args = getattr(case_type, "__match_args__", [])
    unmodified = [node]

    if isinstance(node, ast.Match):
        if ast.unparse(node.subject) != self_name:
            return unmodified

        for case in node.cases:
            if isinstance(case.pattern, ast.MatchClass):
                if ast.unparse(case.pattern.cls) != case_name:
                    continue

                stmts = []
                for i, pattern in enumerate(case.pattern.patterns):
                    if isinstance(pattern, ast.MatchAs):
                        try:
                            attr_name = match_args[i]
                        except IndexError:
                            return unmodified

                        bind = ast.parse(f"{pattern.name} = {self_name}.{attr_name}")
                        stmts.extend(bind.body)
                    else:
                        return [node]

                stmts.extend(case.body)
                return stmts

            elif isinstance(case.pattern, ast.MatchAs):
                if case.pattern.name is None:
                    return case.body
                bind = ast.parse(f"{case.pattern.name} = {self_name}")
                return [*bind.body, *case.body]

    return unmodified
