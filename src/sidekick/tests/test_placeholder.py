from sidekick import _, fn, op, F, record


class TestPlaceholder:
    def test_with_math_operators(self):
        print(dir(_))
        inc = fn(_ + 1)
        assert inc(1) == 2
        assert inc(2) == 3

        half = fn(_ / 2)
        assert half(2) == 1.0
        assert half(4) == 2.0

        inv = fn(1 / _)
        assert inv(2) == 0.5
        assert inv(0.5) == 2.0

        expr = fn(+(2 * _) + 1)
        assert expr(0) == 1.0
        assert expr(1) == 3.0

    def test_multiple_args(self):
        double = fn(_ + _)
        assert double(2) == 4

        poly = fn(_ ** 2 + 2 * _ + 1)
        assert poly(0) == 1
        assert poly(1) == 4

    def test_attr_access(self):
        imag = fn(_.imag)
        assert imag(1) == 0
        assert imag(1j) == 1

    def test_method_call(self):
        bit = fn(_.bit_length())
        assert bit(2) == 2
        assert bit(42) == 6

    def test_function_application(self):
        f = fn(F(abs, _))
        assert f(-1) == 1

    def test_nested_attribute_access(self):
        x = record(foo=record(bar=42))

        assert fn(_.foo.bar == 42)(x) is True
        assert fn(_.foo.bar == 40)(x) is False
        assert fn(_.foo.bar.bit_length())(x) == 6

    def test_nested_algebraic_expresions(self):
        f = fn(_.real + _.imag) 
        assert f(42) == 42
        assert f(21 + 21j) == 42

        f = fn(_.real / (_.real + _.imag))
        assert f(42) == 1.0 
        assert f(21 + 21j) == 0.5 

        f = fn(_.real / (_.real * _.real))
        assert f(2) == 0.5 
        assert f(2 + 2j) == 0.5 