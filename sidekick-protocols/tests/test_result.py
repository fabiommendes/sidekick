import pytest

from sidekick.results import Result, Ok, Err, Just, Nothing
from sidekick.lambdas import X


class TestResults:
    def test_class_hierarchy(self, x=42):
        assert isinstance(Ok(x), Result)
        assert isinstance(Err(x), Result)

    def test_creation(self, x=42):
        assert Result.from_value(x) == Ok(x)
        assert Result.from_value(None) == Ok(None)

        assert Result.from_error(x) == Err(x)
        assert Result.from_error(None) == Err(None)

    def test_mapping_functions(self, x=42):
        kx = Ok(x)
        err = Err(x)

        assert kx.map(X + 1) == Ok(x + 1)
        assert err.map(X + 1) == err

        assert kx.map_error(X + 1) == kx
        assert err.map_error(X + 1) == Err(x + 1)

        assert kx.flatmap(lambda x: Ok(x + 1)) == Ok(x + 1)
        assert err.flatmap(lambda x: Ok(x + 1)) == err

        assert kx.flatmap_error(lambda x: Ok(x + 1)) == kx
        assert err.flatmap_error(lambda x: Ok(x + 1)) == Ok(x + 1)

    def test_flattening(self, x=42):
        kx = Ok(x)
        kkx = Ok(Ok(x))
        kkkx = Ok(Ok(Ok(x)))
        err = Err(x)

        assert kkx.flatten() == kx
        assert kkkx.flatten() == kkx
        assert err.flatten() == err

        # assert kx.flatten_deep() == kx
        # assert kkx.flatten_deep() == kx
        # assert kkkx.flatten_deep() == kx
        # assert err.flatten_deep() == err

    def test_ap(self, x=42):
        kx = Ok(x)
        err = Err(x)

        assert kx.ap(Ok(X + 1)) == Ok(x + 1)
        assert err.ap(Ok(X + 1)) == err
        assert kx.ap(err) == err

    def test_default_getters(self, x=42):
        kx = Ok(x)
        err = Err(x)

        assert kx.value_or(x + 1) == x
        assert err.value_or(x + 1) == x + 1

        assert kx.value_or_call(lambda: x + 1) == x
        assert err.value_or_call(lambda: x + 1) == x + 1

        assert kx.unwrap() == x

        with pytest.raises(ValueError):
            err.unwrap()

        assert kx.attr("imag") == Ok(0)
        assert err.attr("imag") == err

        assert kx.method("bit_count") == Ok(x.bit_count())
        assert err.method("bit_count") == err

    def test_converters(self, x=42):
        kx = Ok(x)
        kxx = Ok([x, x])
        err = Err(x)

        assert list(kxx.iter()) == [x, x]
        assert list(err.iter()) == []

        assert kx.to_result() is kx
        assert err.to_result() is err
        assert err.to_result(ValueError) == Err(ValueError)

        assert kx.to_maybe() == Just(x)
        assert err.to_maybe() == Nothing

    def test_operators_cmp(self, x=21, y=2):
        kx = Ok(x)
        kx_ = Ok(x - 1)
        err = Err(x)

        assert kx == Ok(x)
        assert err == err
        assert kx != err
        assert Result.__eq__(kx, Ok(x))
        assert not Result.__eq__(kx, err)

        assert kx > Ok(x - 1)
        assert kx >= Ok(x - 1)
        assert kx >= Ok(x)
        assert kx > err
        assert err < kx
        assert err < kx
        assert not err < err

        assert sorted([kx, kx_, err]) == [err, kx_, kx]

    def test_operators_arith(self, x=21, y=2):
        kx = Ok(x)
        ky = Ok(y)
        err = Err(x)

        assert kx + ky == Ok(x + y)
        assert kx * ky == Ok(x * y)
        assert kx + err == err
        assert err + err == err
        assert err - err == err

    def test_operators_index(self, x=21, y=2):
        err = Err(x)

        assert Ok([1, 2])[0] == Ok(1)
        assert err[0] == err

        assert x in Ok([x, x + 1])
        assert x not in err

    def test_operators_unary(self, x=21, y=2):
        kx = Ok(x)
        err = Err(x)

        assert +kx == Ok(+x)
        assert -kx == Ok(-x)
        assert ~kx == Ok(~x)
        assert +err == err
        assert -err == err
        assert ~err == err
