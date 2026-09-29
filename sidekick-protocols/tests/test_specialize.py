from dataclasses import dataclass
from types import SimpleNamespace
from sidekick.results.ast_optimizer import specialize_method

decorator = lambda x: x


class Maybe:
    @decorator
    def example(self, /):
        pre = "pre"
        match self:
            case Just(x):
                out = x
            case _:
                out = None
        return pre, out


@dataclass
class Just(Maybe):
    value: int


@dataclass
class Nothing(Maybe):
    ...


class TestSpecialize:
    def test_specialize_case_statement(self, x=42):
        f_just = specialize_method(Maybe.example, Just)
        f_nothing = specialize_method(Maybe.example, Nothing)

        # Specialized version has the same output as the non-specialized one
        assert Maybe.example(Just(x)) == f_just(Just(x)) == ("pre", x)
        assert Maybe.example(Nothing) == f_nothing(Nothing) == ("pre", None)

        # Specialized versions assume self is a Just or Nothing, for each case.
        # Id uses duck typing, instead of an explicit check
        assert f_nothing(Just(x)) == ("pre", None)
        assert f_just(SimpleNamespace(value=x)) == ("pre", x)
