import pytest
from sidekick import fn, _, curry


class TestFn:

    @pytest.fixture
    def double(self):
        return lambda x: 2 * x

    @pytest.fixture
    def fn_double(self, double):
        return fn(double)

    @pytest.fixture
    def fn_inc(self):
        return fn(lambda x: x + 1)

    @pytest.fixture
    def g(self):
        return lambda x, y, z: (x, y, z)

    def test_fn_function_filter_notation(self, fn_double):
        res = (
            2 | fn_double 
              | fn_double
        )
        assert res == 8

    def test_fn_pipeline_notation(self, fn_double, fn_inc):
        func1 = fn_double >> fn_inc
        func2 = fn_inc >> fn_double
        func3 = fn_double << fn_inc
        func4 = fn_inc << fn_double

        # func1 is the same as func4
        assert func1(2) == func4(2) == 5
        assert func1(1) == func4(1) == 3

        # func2 is the same as func3
        assert func2(2) == func3(2) == 6
        assert func2(1) == func3(1) == 4

    def test_fn_starts_a_pipeline(self, double):
        func = fn >> double
        assert func(2) == 4
        assert func(3) == 6

    def test_pipeline_takes_precedence_to_filter_application(self, double):
        assert (2 | fn >> double) == 4

    def test_fn_function_attributes(self):
        @fn
        def f(x):
            "doc"
            return x

        assert f.__name__ == 'f'
        assert f.__doc__ == 'doc'

    def test_fn_partial_function_application(self, g):
        g = fn(g)
        assert g[1](2, 3) == g(1, 2, 3) == (1, 2, 3)
        assert g[1, 2](3) == (1, 2, 3)
        assert g[1, 2, 3]() == (1, 2, 3)

    def test_fn_partial_application_on_creation(self, g):
        assert fn[g](1, 2, 3) == (1, 2, 3)
        assert fn[g, 1](2, 3) == (1, 2, 3)
        assert fn[g, 1, 2](3) == (1, 2, 3)
        assert fn[g, 1, 2, 3]() == (1, 2, 3)
        
    def test_fn_partial_application_with_placehlder(self, g):
        assert fn[g, _, 2, 3](1) == (1, 2, 3)
        assert fn[g, 1, _, 3](2) == (1, 2, 3)
        assert fn[g, 1, 2, _](3) == (1, 2, 3)
        
        assert fn[g, _, _, 2](1) == (1, 1, 2)
        assert fn[g, 1, _, _](2) == (1, 2, 2)
        assert fn[g, _, 2, _](1) == (1, 2, 1)

    def test_curry_decorator(self, g):
        g = curry(g)
        assert g(1, 2, 3) == (1, 2, 3)
        assert g(1)(2)(3) == (1, 2, 3)
        assert g(1, 2)(3) == (1, 2, 3)
        assert g(1)(2, 3) == (1, 2, 3)

    def test_curried_fn_functions(self, g):
        assert fn.curried(g)(1, 2, 3) == (1, 2, 3)
        assert fn.curried(g)(1)(2)(3) == (1, 2, 3)
        assert fn.curried(g)(1, 2)(3) == (1, 2, 3)
        assert fn.curried(g)(1)(2, 3) == (1, 2, 3)

    def test_fn_accepts_attribute_assignment(self, g):
        g = fn(g)
        g.foo = 'foo'
        assert g.foo == 'foo'

    def test_fn_preserves_function_attributes(self):
        def foo(x):
            return x

        foo.attr = 'foo'

        g = fn(foo)
        assert g.__name__ == 'foo'
        assert g.attr == 'foo'
    
