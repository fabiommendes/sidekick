from collections import OrderedDict
from types import FunctionType

import pytest

from sidekick import *
from sidekick import placeholder as _, always


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
