import operator

import pytest

from sidekick import placeholder as _, fn, F, record, lazy
from sidekick._placeholder import (
    simplify_ast,
    Placeholder,
    Call,
    Cte,
    GetAttr,
    Call,
    compile_ast,
)

func = lambda x: x.__inner_function__


class TestPlaceholder:
    def test_basic_properties(self):
        assert str(+(_.method(42 + _))) == "(+_.method(42 + _))"

    def test_with_math_operators(self):
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

        f = fn(F(dict, [], foo=_))
        assert f("bar") == {"foo": "bar"}

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

        f = fn(-_)
        assert f(2) == -2

        f = fn(-(2 * _))
        assert f(2) == -4

        f = fn((2 * _).imag)
        assert f(2) == 0


class TestPlaceholderCompiler:
    def test_compiler_simplifications(self):
        assert simplify_ast(Placeholder(Cte(42)).imag._ast) == Cte(0)


class TestThisPlaceholder:
    @pytest.fixture(scope="class")
    def cls(self):
        class Cls:
            sum = lazy(_.x + _.y)

            def __init__(self, x, y):
                self.x, self.y = x, y

        return Cls

    @pytest.fixture
    def instance(self, cls):
        return cls(1, 2)

    def test_this_descriptor_works(self, instance):
        assert instance.sum == 3
