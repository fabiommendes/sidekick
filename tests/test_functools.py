from collections import OrderedDict

from sidekick.experimental.function_dispatch import lazy_singledispatch


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
