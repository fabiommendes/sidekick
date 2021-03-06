import operator as op

import pytest

import sidekick.api as sk
from sidekick import X
from sidekick.seq.testing import VALUE, LL


class TestBasic:
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
            sk.only(default=VALUE): VALUE,
            sk.last(n=2, default=None): (None, None),
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
            sk.last(n=2): (4, 5),
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

    def test_only(self):
        assert sk.only([42]) == 42
        assert sk.only([], default=42) == 42

        with pytest.raises(ValueError):
            sk.only([])

        with pytest.raises(ValueError):
            sk.only([1, 2])


class TestCreation:
    def test_unfold(self):
        assert sk.unfold(lambda x: None if x > 10 else (2 * x, x), 1) == LL(1, 2, 4, 8)

    def test_nums(self):
        assert sk.nums() == LL(0, 1, 2, 3, 4, ...)
        assert sk.nums(1) == LL(1, 2, 3, 4, 5, ...)
        assert sk.nums(1, ...) == LL(1, 2, 3, 4, 5, ...)
        assert sk.nums(1, 2, ...) == LL(1, 2, 3, 4, 5, ...)
        assert sk.nums(1, 3, ...) == LL(1, 3, 5, 7, 9, ...)
        assert sk.nums(1, 2, 3, 5, ...) == LL(1, 2, 3, 5, 7, 9, ...)

    def test_iterate(self):
        # Test special cases for 0, 1, 2, 3, and more past values
        fn = lambda *args: sum(args)
        assert sk.iterate((X + 1), 1) == LL(1, 2, 3, ...)
        assert sk.iterate(fn, 1, 1) == LL(1, 1, 2, 3, 5, 8, ...)
        assert sk.iterate(fn, 1, 3) == LL(1, 3, 4, 7, 11, ...)
        assert sk.iterate(fn, 1, 1, 1) == LL(1, 1, 1, 3, 5, 9, 17, ...)
        assert sk.iterate(fn, 1, 1, 1, 1) == LL(1, 1, 1, 1, 4, 7, 13, 25, ...)

        assert sk.iterate(op.mul, 1, index=1) == LL(1, 1, 2, 6, 24, 120, ...)
        assert sk.iterate(fn, 1, index=sk.nums()) == LL(1, 1, 2, 4, 7, 11, 16, ...)


class TestHypothesis:
    FN_PRED_SEQ = {}
    FN_SELECTOR = {}

    def test_functions_that_do_not_change_size_of_iterables(self):
        ...

    def test_functions_that_filter_iterables(self):
        filters = [
            sk.filter,
            sk.remove,
            sk.dedupe,
            sk.unique,
            sk.take,
            sk.rtake,
            sk.drop,
            sk.rdrop,
        ]

    def test_functions_that_filter_and_transform_iterables(self):
        ...
