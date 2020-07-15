import pytest

from sidekick import (
    Result,
    Ok,
    Err,
    to_result,
    X,
    Just,
    Nothing,
    rapply,
    Y,
    first_error,
    rpipe,
    error,
    rpipeline,
)
from sidekick.types.result import results


class TestResult:
    def test_result_type(self):
        ok = Ok(42)

        assert ok == Ok(42)
        assert ok != Err(42)

        assert ok.map((X * 2)) == Ok(84)
        assert ok.map_error((X * 2)) is ok
        assert ok.map_exception((X * 2)) is ok
        assert ok.check_error() is None
        assert ok.error is None

        assert ok.method("bit_length") == Ok(6)
        assert ok.attr("denominator") == Ok(1)
        assert list(Ok([1, 2, 3]).iter()) == [1, 2, 3]
        assert ok.to_result() is ok
        assert ok.to_maybe() == Just(42)

    def test_error_state(self):
        err = Err("error")
        exc = Err(ValueError)
        exc_ = Err(ValueError("foo"))

        assert exc.catches(ValueError)
        assert exc_.catches(ValueError)
        assert err.flip() == Ok("error")

        assert err.map((X * 2)) is err
        assert str(err.map_error(ValueError)) == str(Err(ValueError("error")))
        assert str(err.map_exception(ValueError)) == str(Err(ValueError("error")))
        assert exc.map_exception(IndexError) is exc
        assert exc_.map_exception(IndexError) is exc_

        for e in [err, exc, exc_]:
            with pytest.raises(ValueError):
                e.check_error()

            with pytest.raises(ValueError):
                e.value

        assert err.method("bit_length") is err
        assert err.attr("denominator") is err
        assert list(err.iter()) == []
        assert err.to_maybe() is Nothing

    def test_result_functions(self):
        ok = Ok(42)
        err = Err("error")
        div = lambda x, y: Ok(x / y) if y else Err("math")
        div_err = rpipeline((X / Y))
        div_err2 = rpipeline((X / Y), str)
        half = lambda x: rapply((X / 2), x)
        half_err = lambda x: x // 2 if x % 2 == 0 else error("odd")

        assert first_error([1, 2, 3]) is None

        assert rapply(div, ok, err) is err
        assert rapply((X / Y), 1, 2) == Ok(0.5)
        assert rapply((X / Y), ok, 2) == Ok(21)

        assert rpipe(1.0, (X / 2), str) == Ok("0.5")
        assert rpipe(1.0, half, str) == Ok("0.5")
        assert rpipe(ok, (X / 2), str) == Ok("21.0")
        assert rpipe(ok, half, str) == Ok("21.0")
        assert rpipe(ok, (X / 0)).catches(ZeroDivisionError)
        assert rpipe(42, half_err) == Ok(21)
        assert rpipe(21, half_err).catches(ValueError)
        assert rpipe(err, half_err) is err

        assert div_err(1, 0).catches(ZeroDivisionError)
        assert div_err(1, 2) == Ok(0.5)
        assert div_err2(1, 0).catches(ZeroDivisionError)
        assert div_err2(1, 2) == Ok("0.5")

        assert first_error(1, 2, 3) is None
        assert first_error(ok, 2, 3) is None
        assert first_error(ok, err, 3) is "error"
        assert first_error(IndexError, 1, 2) is IndexError

    def test_catch_exceptions_block(self):
        with results() as res:
            x = int("a")
            res.append(x / 2)

        assert res.value.catches(ValueError)
        assert res

        with results() as res:
            x = int(3.14)
            res.append(x / 2)

        assert res.value == Ok(1.5)
        assert res

        with pytest.raises(ValueError):
            with results(ZeroDivisionError) as res:
                res.append(int("1/0"))

        assert res.value.catches(RuntimeError)
        assert not res
