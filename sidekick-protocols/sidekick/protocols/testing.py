from typing import TypeVar

from hypothesis import strategies as st
from hypothesis import given

from .protocols import Functor
from .util import a

F = TypeVar("F", bound=Functor)


def identity(x: a) -> a:
    return x


def int_functor(functor) -> st.SearchStrategy[Functor[int]]:
    """
    Store integer values in functor.
    """
    return st.integers().flatmap(
        lambda i: functor.map(lambda f: f.__functor_map__(lambda _: i))
    )


def functor_laws_tester(functor: st.SearchStrategy[F]) -> type:
    class TestFunctorLaws:
        """
        Test if functor preserves functor laws.
        """

        @given(functor)
        def test_functor_map_preserves_identity(self, fa: Functor):
            assert fa.__functor_map__(identity) == fa

        @given(int_functor(functor))
        def test_functor_map_preserves_composition(self, fi: Functor):
            f = lambda x: x + 1
            g = lambda x: 2 * x
            fog = lambda x: f(g(x))
            assert fi.__functor_map__(fog) == fi.__functor_map__(g).__functor_map__(f)

    return TestFunctorLaws
