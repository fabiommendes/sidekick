import pytest

import sidekick as sk
from sidekick import X, Y, L


class EqList(list):
    def __eq__(self, other):
        if self and self[-1] == ...:
            other = sk.take(len(self) - 1, other)
            self = self[:-1]
        other = list(other)
        assert list.__eq__(self, other), f"Different outputs: {other} != {self}"
        return True


LL = lambda *args: EqList(args)
VALUE = type("VALUE", (), {"__repr__": lambda self: "VALUE"})()


# ==============================================================================
# ITERTOOLS: basic.py
# ==============================================================================


class TestBasicFunctions:
    def test_fail_with_empty_lists(self, empty):
        fail = [sk.uncons, sk.first, sk.second, sk.last, sk.nth(0), sk.nth(1)]

        for func in fail:
            with pytest.raises(ValueError):
                print("not failed:", func, func(empty()))

    def test_succeed_with_empty_lists(self, empty):
        success = {
            sk.cons(1): LL(1),
            sk.uncons(default=VALUE): (VALUE, LL()),
            sk.first(default=VALUE): VALUE,
            sk.second(default=VALUE): VALUE,
            sk.last(default=VALUE): VALUE,
            sk.nth(0, default=VALUE): VALUE,
            sk.nth(5, default=VALUE): VALUE,
            sk.init: LL(),
            sk.rest: LL(),
            sk.last_n(2): (),
            sk.is_empty: True,
            sk.length: 0,
        }
        for f, v in success.items():
            assert f(empty()) == v

    def test_succeed_with_seq_of_numbers(self, nums):
        success = {
            sk.cons(0): LL(0, 1, 2, 3, 4, 5),
            sk.uncons: (1, LL(2, 3, 4, 5)),
            sk.first: 1,
            sk.second: 2,
            sk.last: 5,
            sk.nth(0): 1,
            sk.nth(2): 3,
            sk.nth(5, default=VALUE): VALUE,
            sk.init: LL(1, 2, 3, 4),
            sk.rest: LL(2, 3, 4, 5),
            sk.last_n(2): (4, 5),
            sk.is_empty: False,
            sk.length: 5,
            sk.length(limit=2): 2,
        }
        for f, v in success.items():
            assert f(nums()) == v

    def test_fail_seq_of_numbers(self, nums):
        fail = [sk.nth(5), sk.nth(10)]

        for func in fail:
            with pytest.raises(ValueError):
                v = func(nums())
                print("not failed:", func, v)


# ==============================================================================
# ITERTOOLS: creation.py
# ==============================================================================


class TestCreation:
    def test_unfold(self):
        # Finite list
        assert sk.unfold(lambda x: None if x > 10 else (2 * x, x), 1) == LL(1, 2, 4, 8)

    def test_iterate_past(self):
        # Test special cases for 0, 1, 2, 3, and more past values
        assert sk.iterate_past(lambda: 42, ()) == LL(42, 42, 42, ...)
        assert sk.iterate_past(lambda x: x + 1, [1]) == LL(1, 2, 3, ...)
        assert sk.iterate_past(lambda x, y: x + y, [1, 3]) == LL(1, 3, 4, 7, ...)

        assert sk.iterate_past(lambda x, y, z: x + y + z, [1, 1, 1]) == LL(
            1, 1, 1, 3, 5, 9, 17, ...
        )

        assert sk.iterate_past(lambda x, y, z, w: x + y + z + w, [1, 1, 1, 1]) == LL(
            1, 1, 1, 1, 4, 7, 13, 25, ...
        )

    def test_iterate_indexed(self, nums):
        assert sk.iterate_indexed((X + Y), 1, idx=nums()) == LL(1, 2, 4, 7, 11, 16)
