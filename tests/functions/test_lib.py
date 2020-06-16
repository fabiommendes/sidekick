import operator as op
from inspect import Signature

from sympy.utilities import pytest

import sidekick.api as sk
from sidekick.api import X


class TestIntrospection:
    def test_arity(self):
        assert sk.arity(lambda x, y: None) == 2

    def test_signature(self):
        sig: Signature = sk.signature(lambda x, y: None)
        assert sig.return_annotation == sig.empty
        assert list(sig.parameters) == ["x", "y"]

    def test_stub(self):
        def add(x: float, y: float) -> float:
            return x + y

        stub = sk.stub(add)
        assert str(stub) == "def add(x: float, y: float) -> float: ..."


class TestCombinators:
    def test_always(self):
        f = sk.always(42)
        assert f() == 42
        assert f(1) == 42
        assert f(1, 2, 3) == 42
        assert f(1, 2, 3, more=4) == 42

    def test_identity_functions(self):
        obj = object()
        assert sk.identity(obj) is obj
        assert sk.identity(obj, "other") is obj
        assert sk.ridentity(obj) is obj
        assert sk.ridentity("other", obj) is obj

    def test_rec(self):
        fat = sk.rec(lambda f, n: 1 if n == 0 else n * f(f, n - 1))
        assert fat(5) == 120

        # Does not depend on binding names
        assert sk.rec(lambda f, n: 1 if n == 0 else n * f(f, n - 1))(5) == 120

    def test_power(self):
        f = lambda x: 2 * x
        assert sk.power(f, 0)(3) == 3
        assert sk.power(f, 1)(3) == 6
        assert sk.power(f, 2)(3) == 12
        assert sk.power(f, 3)(3) == 24


class TestComposition:
    def test_compose(self):
        f = sk.compose((X + 1), (X * 2))
        assert f(1) == 3
        assert f(2) == 5

    def test_pipe(self):
        assert sk.pipe(2, (X + 1), (X * 2)) == 6

    def test_pipeline(self):
        f = sk.pipeline((X + 1), (X * 2))
        assert f(1) == 4
        assert f(2) == 6

    def test_thread(self):
        assert sk.thread(20, (op.truediv, 2), (op.add, 2)) == 12

    def test_rthread(self):
        assert sk.rthread(20, (op.truediv, 2), (op.add, 2)) == 2.1


class TestPartialApplication:
    def test_partial(self):
        f = sk.partial(op.truediv, 12)
        assert f(1) == 12
        assert f(2) == 6
        assert f(3) == 4
        assert f(4) == 3

    def test_rpartial(self):
        f = sk.rpartial(op.truediv, 12)
        assert f(1) == 1 / 12
        assert f(2) == 1 / 6
        assert f(3) == 1 / 4
        assert f(4) == 1 / 3

    def test_curry(self):
        def f(x, y, z):
            return x + 2 * y + 3 * z

        g = sk.curry(3, f)
        assert g(1, 2, 3) == 14
        assert g(1)(2)(3) == 14
        assert g(1)(2, 3) == 14

    def test_curry_detects_variadic_functions(self):
        with pytest.raises(TypeError):
            sk.curry(..., lambda *args: args)
