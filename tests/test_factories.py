from sidekick import caller, attrgetter


class TestCaller:
    def test_simple_caller(self):
        f = caller(42)
        assert f(abs) == 42

    def test_nested_caller(self):
        f = caller.real.conjugate()
        assert f(42) == 42

    def test_very_nested_caller(self):
        f = caller.real.imag.conjugate()
        assert f(42) == 0


class TestAttrGetter:
    def test_nested_attr_getter(self):
        f = attrgetter.real.imag.real.imag
        assert f.__attrs__ == ('real', 'imag', 'real', 'imag')
        assert f(42) == 0
