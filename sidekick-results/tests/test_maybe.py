from types import SimpleNamespace

import pytest

from sidekick.results import Maybe, Just, Nothing, Ok, Err
from sidekick.lambdas import X


class TestMaybe:
    def test_maybe_class_hierarchy(self, x=42):
        assert isinstance(Just(x), Maybe)
        assert isinstance(Nothing, Maybe)

    def test_creation_of_maybes(self, x=42):
        assert Maybe.from_value(x) == Just(x)
        assert Maybe.from_value(None) == Just(None)

        assert Maybe.from_optional(x) == Just(x)
        assert Maybe.from_optional(None) == Nothing

        assert Maybe(x) == Just(x)
        assert Maybe(None) == Nothing

    def test_mapping_functions(self, null, x=42):
        jx = Just(x)

        assert jx.map(X + 1) == Just(x + 1)
        assert null.map(X + 1) == null

        assert jx.map_error(X + 1) == jx
        assert null.map_error(X + 1) == null

        assert jx.flatmap(lambda x: Just(x + 1)) == Just(x + 1)
        assert jx.flatmap(lambda x: None) == null
        assert null.flatmap(lambda x: Just(x + 1)) == null

        assert jx.flatmap_error(X + 1) == jx
        assert null.flatmap_error(X + 1) == null

    def test_flattening(self, null, x=42):
        jx = Just(x)
        jjx = Just(Just(x))
        jjjx = Just(Just(Just(x)))

        assert jjx.flatten() == jx
        assert jjjx.flatten() == jjx
        assert null.flatten() == null

        assert jx.flatten_deep() == jx
        assert jjx.flatten_deep() == jx
        assert jjjx.flatten_deep() == jx
        assert null.flatten_deep() == null

        assert Just(None).flatten_deep() == null

    def test_ap(self, null, x=42):
        jx = Just(x)

        assert jx.ap(Just(X + 1)) == Just(x + 1)
        assert null.ap(Just(X + 1)) == null
        assert jx.ap(null) == null

    def test_default_getters(self, null, x=42):
        jx = Just(x)

        assert jx.value_or(x + 1) == x
        assert null.value_or(x + 1) == x + 1

        assert jx.value_or_call(lambda: x + 1) == x
        assert null.value_or_call(lambda: x + 1) == x + 1

        assert jx.unwrap() == x

        with pytest.raises(ValueError):
            null.unwrap()

        assert jx.attr("imag") == Just(0)
        assert null.attr("imag") == null
        assert Just(SimpleNamespace(attr=None)).attr("attr") == null

        assert jx.method("bit_count") == Just(x.bit_count())
        assert null.method("bit_count") == null
        assert Just(SimpleNamespace(attr=None)).attr("attr") == null

    def test_converters(self, null, x=42):
        jx = Just(x)
        jxx = Just([x, x])

        assert list(jxx.iter()) == [x, x]
        assert list(null.iter()) == []

        assert jx.to_result() == Ok(x)
        assert null.to_result() == Err(Exception)
        assert null.to_result(ValueError) == Err(ValueError)

        assert jx.to_maybe() is jx
        assert null.to_maybe() is null

    def test_operators_cmp(self, null, x=21, y=2):
        jx = Just(x)
        jx_ = Just(x - 1)

        assert jx == Just(x)
        assert null == null
        assert jx != null
        assert Maybe.__eq__(jx, Just(x))
        assert not Maybe.__eq__(jx, null)

        assert jx > Just(x - 1)
        assert jx >= Just(x - 1)
        assert jx >= Just(x)
        assert jx > null
        assert null < jx
        assert null < jx
        assert not null < null

        assert sorted([jx, jx_, null]) == [null, jx_, jx]

    def test_operators_arith(self, null, x=21, y=2):
        jx = Just(x)
        jy = Just(y)

        assert jx + jy == Just(x + y)
        assert jx * jy == Just(x * y)
        assert jx + null == null
        assert null + null == null
        assert null - null == null

    def test_operators_index(self, null, x=21, y=2):
        assert Just([1, 2])[0] == Just(1)
        assert null[0] == null

        assert x in Just([x, x + 1])
        assert x not in null

    def test_operators_unary(self, null, x=21, y=2):
        jx = Just(x)

        assert +jx == Just(+x)
        assert -jx == Just(-x)
        assert ~jx == Just(~x)
        assert +null == null
        assert -null == null
        assert ~null == null
