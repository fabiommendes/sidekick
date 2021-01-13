import operator as op
import time
from inspect import Signature

import pytest

import sidekick.api as sk
from sidekick import Nothing, Just
from sidekick import placeholder as _
from sidekick.api import X, Y
from types import FunctionType


class TestCoreFunctions:
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

    def test_force_function_converts_placeholder(self):
        for conv in [sk.to_fn, sk.to_callable, sk.to_function]:
            inc = conv(_ + 1)
            assert callable(inc)
            assert inc(1) == 2

        assert type(inc) is FunctionType

    def test_to_function_converts_callable(self):
        class Inc:
            def __call__(self, x):
                return x + 1

        inc = Inc()
        inc_f = sk.to_function(inc, "inc")
        assert inc(1) == 2
        assert inc_f(1) == 2
        assert type(inc_f) is FunctionType
        assert inc_f.__name__ == "inc"
        assert sk.to_function(inc).__name__ == "Inc"

        # Lambdas and name control
        assert sk.to_function(_ + 1, "fn").__name__ == "fn"
        assert sk.to_function(lambda n: n + 1, "fn").__name__ == "fn"


class TestFnAPIMethods:
    def test_fn_operators(self):
        fn = sk.fn
        id = lambda x: x
        for a, b in [(fn, fn), (fn, id), (id, fn)]:
            f = a(X < 10)
            g = b(X > 0)
            assert (h := f & g)(5) and not h(20) and not h(-1)
            assert (h := f | g)(5) and h(20) and h(-1)
            assert not (h := f ^ g)(5) and h(20) and h(-1)

    def test_fn_core_attributes(self):
        ...

    def test_fn_methods_for_argument_selection(self):
        f = sk.fn(op.add)
        g = sk.fn(op.sub)
        h = sk.fn(sum)

        # Arg selection
        assert g(1, 3) == g.flip(3, 1)
        assert g(1, 3) == g.reverse_args(3, 1)
        assert f.select_args([1, 2], 1, 2, 4, 8) == 6
        assert f.select_args([1, 2])(1, 2, 4, 8) == 6
        assert f.skip_args(2, 1, 2, 4, 8) == 12
        assert f.skip_args(2)(1, 2, 4, 8) == 12
        assert f.keep_args(2, 1, 2, 4, 8) == 3
        assert f.keep_args(2)(1, 2, 4, 8) == 3
        assert f.keep_args(2)(1, 2, 4, 8) == 3
        assert f.splice_args([1, 2]) == 3
        assert f.splice_args([1], 2) == 3
        assert f.set_null(1, 2)(None, 3) == 4
        assert h.variadic_args(1, 2, 3, 4) == 10

    def test_fn_methods_for_function_composition(self):
        f = sk.fn(op.add)
        assert f.do(1, 2) == 1

        g = sk.fn(X + 1)
        assert g.compose(g)(1) == 3
        assert g.pipeline(g, g, g)(1) == 5
        assert g.juxt(g, g, g)(1) == (2, 2, 2, 2)

    def test_fn_methods_runtime_modification(self):
        f = sk.fn(op.add)
        g = f.once()

        assert g(1, 3) == f(1, 3) == 4
        assert g(1, 5) == 4
        assert f(1, 5) == 6

        lst = [1, 2, 3]
        f = sk.fn(lst.pop).thunk(1)
        assert lst == [1, 2, 3]
        assert f() == 2 and lst == [1, 3]

        lst = [1, 2, 3]
        f = sk.fn(lst.pop).call_after(2)
        assert f() is None and lst == [1, 2, 3]
        assert f() is None and lst == [1, 2, 3]
        assert f() == 3 and lst == [1, 2]

        lst = [1, 2, 3]
        f = sk.fn(lst.pop).call_at_most(3)
        assert f() == 3 and lst == [1, 2]
        assert f() == 2 and lst == [1]
        assert f() == 1 and lst == []
        assert f() == 1 and lst == []


class TestFunctionalInterfaces:
    def test_algebra_instances(self):
        assert sk.semigroup[list]([], [1], [2, 3]) == [1, 2, 3]
        assert sk.monoid[list]([], [1], [2, 3]) == [1, 2, 3]
        assert sk.group["+"](1, 2, 3, 4, 5) == 15
        assert sk.group["*"](1, 2, 3, 4, 5) == 120

    def test_functor_instances(self):
        assert sk.apply[list](X + 1, [1, 2, 3]) == [2, 3, 4]

    def test_applicative_instances(self):
        assert sk.apply[list]((X + Y), [1, 2], [3, 4]) == [4, 5, 5, 6]

    def test_monad_instances(self):
        assert sk.apply_flat[list](lambda n: [n, n], [1, 2, 3]) == [1, 1, 2, 2, 3, 3]


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

    def test_trampoline(self):
        @sk.trampoline
        def fat(n, acc=1):
            if n > 0:
                return n - 1, acc * n
            else:
                raise StopIteration(acc)


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

    def test_thread_if(self):
        assert sk.thread_if(20, (0, op.truediv, 2), (1, op.sub, 2)) == 18

    def test_rthread_if(self):
        assert sk.rthread_if(20, (0, op.truediv, 2), (1, op.sub, 2)) == -18

    def test_juxt(self):
        f = sk.juxt(X, 2 * X, 3 * X)
        assert f(1) == (1, 2, 3)
        assert f(2) == (2, 4, 6)


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


class TestRuntime:
    def test_once(self):
        lst = [1, 2, 3]
        fn = sk.once(lst.pop)
        assert fn(0) == 1
        assert fn(-1) == 1
        assert lst == [2, 3]

    def test_thunk(self):
        lst = [1, 2, 3]
        fn = sk.thunk(lst.pop, 0)
        assert fn() == 1
        assert fn() == 1
        assert lst == [2, 3]

    def test_thunk_decorator(self):
        lst = [1, 2, 3]

        @sk.thunk(..., 0)
        def fn(i):
            return lst.pop(i)

        assert fn() == 1
        assert fn() == 1
        assert lst == [2, 3]

    def test_call_after(self):
        lst = [1, 2, 3]
        fn = sk.call_after(2)(lst.pop)
        assert fn() is None
        assert fn() is None
        assert fn() == 3
        assert lst == [1, 2]

    def test_call_at_most(self):
        lst = [1, 2, 3]
        fn = sk.call_at_most(len(lst))(lst.pop)
        assert fn(0) == 1
        assert fn() == 3
        assert fn(0) == 2
        assert fn() == 2
        assert lst == []

    def test_background(self):
        # Compute values
        f = sk.background(lambda x: x * x)
        res = f(10)
        assert callable(res)
        assert res() == 100
        assert res.maybe() == Just(100)

        # Is non-blocking
        g = sk.background(time.sleep)
        t0 = time.time()
        g(1)
        assert time.time() - t0 < 0.1

        # Timeout works
        g = sk.background(time.sleep, timeout=0.01)
        res = g(1)
        with pytest.raises(TimeoutError):
            res()
        assert res.maybe() is Nothing

    def test_throttle(self):
        f = sk.throttle(0.01, lambda x: x * x)
        assert (f(2), f(3), f(4)) == (4, 4, 4)

        time.sleep(0.0125)
        assert f(3) == 9
        assert f(4) == 9
