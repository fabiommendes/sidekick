from collections import OrderedDict
from types import FunctionType

import pytest

from sidekick import *
from sidekick import placeholder as _


class TestLazySingleDispatch:
    def test_single_dispatch_example(self):
        @lazy_singledispatch
        def foo(x):
            return 42

        @foo.register(str)
        def _str(x):
            return x

        @foo.register("collections.OrderedDict")
        def _map(x):
            return dict(x)

        d = OrderedDict({3: "three"})
        assert foo(1) == 42
        assert foo("two") == "two"
        assert foo(d) == d
        assert type(foo(d)) is dict


class TestLibFunctions:
    def test_force_function_converts_placeholder(self):
        inc = force_function(_ + 1)
        assert type(inc) is FunctionType
        assert force_function(lambda x: x + 1, "inc").__name__ == "inc"

    def test_force_function_converts_callable(self):
        class Inc:
            def __call__(self, x):
                return x + 1

        inc = Inc()
        inc_f = force_function(inc, "inc")
        assert inc(1) == 2
        assert inc_f(1) == 2
        assert type(inc_f) is FunctionType
        assert inc_f.__name__ == "inc"
        assert force_function(inc).__name__ == "Inc"

    def test_rpartial(self):
        f = rpartial(lambda *args: args, 2, 3)
        assert f(1) == (1, 2, 3)

    def test_identity(self):
        obj = object()
        assert identity(obj) is obj

    def test_juxt(self):
        f = juxt(_, 2 * _, 3 * _)
        assert f(1) == (1, 2, 3)
        assert f(2) == (2, 4, 6)

    def test_const(self):
        f = always(42)
        assert f() == 42
        assert f(1) == 42
        assert f(1, 2, 3) == 42
        assert f(1, 2, 3, more=4) == 42

    def test_curry(self):
        def f(x, y, z):
            return x + 2 * y + 3 * z

        g = curry(3, f)
        assert g(1, 2, 3) == 14
        assert g(1)(2)(3) == 14
        assert g(1)(2, 3) == 14

    def test_curry_detects_variadic_functions(self):
        with pytest.raises(TypeError):
            curry(..., lambda *args: args)
