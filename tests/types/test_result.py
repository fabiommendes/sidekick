import pytest

from sidekick import (
    Result,
    Ok,
    Err,
    result,
    X,
    Just,
    Nothing,
    rapply,
    Y,
    first_error,
    rpipe,
    error,
    rpipeline,
    catch_exceptions,
)


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

        assert exc == ValueError
        assert exc_ == ValueError
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
        assert rpipe(ok, (X / 0)) == ZeroDivisionError
        assert rpipe(42, half_err) == Ok(21)
        assert rpipe(21, half_err) == ValueError
        assert rpipe(err, half_err) is err

        assert div_err(1, 0) == ZeroDivisionError
        assert div_err(1, 2) == Ok(0.5)
        assert div_err2(1, 0) == ZeroDivisionError
        assert div_err2(1, 2) == Ok("0.5")

        assert first_error(1, 2, 3) is None
        assert first_error(ok, 2, 3) is None
        assert first_error(ok, err, 3) is "error"
        assert first_error(IndexError, 1, 2) is IndexError

    def test_catch_exceptions_block(self):
        with catch_exceptions() as err:
            x = int("a")
            err.put(x / 2)

        assert err.get() == ValueError
        assert err

        with catch_exceptions() as err:
            x = int(3.14)
            err.put(x / 2)

        assert err.get() == Ok(1.5)
        assert not err

        with pytest.raises(ValueError):
            with catch_exceptions(ZeroDivisionError) as err:
                err.put(int("1/0"))

        assert err.get() == ValueError
        assert err
