import operator as op
from functools import partial
import pytest

# import sidekick.api as sk
# from sidekick import X
from sidekick.seq.testing import VALUE, LL
from sidekick import seq

class TestBasic:
    def test_fail_with_empty_lists(self, empty):
        fail = [seq.uncons, seq.first, seq.second, seq.last, lambda x: seq.nth(0, x), lambda x: seq.nth(1, x)]

        for func in fail:
            with pytest.raises(ValueError):
                print("not failed:", func, func(empty()))

    def test_succeed_with_empty_lists(self, empty):
        success = {
            partial(seq.cons, 1): LL(1),
            partial(seq.uncons, default=VALUE): (VALUE, LL()),
            partial(seq.first, default=VALUE): VALUE,
            partial(seq.second, default=VALUE): VALUE,
            partial(seq.last, default=VALUE): VALUE,
            partial(seq.nth, 0, default=VALUE): VALUE,
            partial(seq.nth, 5, default=VALUE): VALUE,
            partial(seq.only, default=VALUE): VALUE,
            partial(seq.last_n, 2, default=None): [None, None],
            seq.is_empty: True,
            seq.length: 0,
        }
        for f, v in success.items():
            assert f(empty()) == v

    def test_succeed_with_seq_of_numbers(self, nums_5):
        success = {
            partial(seq.cons, 0): LL(0, 1, 2, 3, 4, 5),
            seq.uncons: (1, LL(2, 3, 4, 5)),
            seq.first: 1,
            seq.second: 2,
            seq.last: 5,
            partial(seq.nth, 0): 1,
            partial(seq.nth, 2): 3,
            partial(seq.nth, 5, default=VALUE): VALUE,
            partial(seq.last_n, 2): [4, 5],
            seq.is_empty: False,
            seq.length: 5,
            partial(seq.length, limit=2): 2,
        }
        for f, v in success.items():
            assert f(nums_5()) == v

    def test_fail_seq_of_numbers(self, nums_5):
        fail = [lambda xs: seq.nth(5, xs), lambda xs: seq.nth(10, xs)]

        for func in fail:
            with pytest.raises(ValueError):
                v = func(nums_5())
                print("not failed:", func, v)

    def test_only(self):
        assert seq.only([42]) == 42
        assert seq.only([], default=42) == 42

        with pytest.raises(ValueError):
            seq.only([])

        with pytest.raises(ValueError):
            seq.only([1, 2])


class TestCreation:
    def test_unfold(self):
        assert seq.unfold(lambda x: None if x > 10 else (2 * x, x), 1) == LL(1, 2, 4, 8)

    def test_nums(self):
        assert seq.nums() == LL(0, 1, 2, 3, 4, ...)
        assert seq.nums(1) == LL(1, 2, 3, 4, 5, ...)
        assert seq.nums(1, ...) == LL(1, 2, 3, 4, 5, ...)
        assert seq.nums(1, 2, ...) == LL(1, 2, 3, 4, 5, ...)
        assert seq.nums(1, 3, ...) == LL(1, 3, 5, 7, 9, ...)
        assert seq.nums(1, 2, 3, 5, ...) == LL(1, 2, 3, 5, 7, 9, ...)

    def test_iterate(self):
        # Test special cases for 0, 1, 2, 3, and more past values
        fn = lambda *args: sum(args)
        assert seq.iterate((lambda x: x + 1), 1) == LL(1, 2, 3, ...)
        assert seq.iterate(fn, 1, 1) == LL(1, 1, 2, 3, 5, 8, ...)
        assert seq.iterate(fn, 1, 3) == LL(1, 3, 4, 7, 11, ...)
        assert seq.iterate(fn, 1, 1, 1) == LL(1, 1, 1, 3, 5, 9, 17, ...)
        assert seq.iterate(fn, 1, 1, 1, 1) == LL(1, 1, 1, 1, 4, 7, 13, 25, ...)

        assert seq.iterate(op.mul, 1, index=1) == LL(1, 1, 2, 6, 24, 120, ...)
        assert seq.iterate(fn, 1, index=seq.nums()) == LL(1, 1, 2, 4, 7, 11, 16, ...)


class TestHypothesis:
    FN_PRED_SEQ = {}
    FN_SELECTOR = {}

    def test_functions_that_do_not_change_size_of_iterables(self):
        ...

    def test_functions_that_filter_iterables(self):
        filters = [
            seq.filter,
            seq.remove,
            seq.dedupe,
            seq.unique,
            seq.take,
            seq.rtake,
            seq.drop,
            seq.rdrop,
        ]

    def test_functions_that_filter_and_transform_iterables(self):
        ...
