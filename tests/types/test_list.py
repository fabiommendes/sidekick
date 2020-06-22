import pytest

from sidekick import List, Nil, X
from sidekick.builtins import getattr


class TestLinkedLists:
    def test_basic_list_structure(self):
        ls = List([1, 2])
        assert ls.head == 1
        assert ls.tail.tail == Nil

    def test_sequence_api(self):
        lst = List([1, 2, 3])

        # Operators
        assert lst == List([1, 2, 3])
        assert lst != List([1, 2, 3, 4])
        assert lst != List([2, 3, 4])
        assert repr(lst) == "List([1, 2, 3])"
        assert len(lst) == 3
        assert lst[0] == 1
        assert lst[2] == 3
        assert lst + List([4, 5]) == List([1, 2, 3, 4, 5])
        assert lst * 2 == List([1, 2, 3, 1, 2, 3])
        assert lst * 1 == lst
        assert lst * 0 == List()
        assert lst > List([0, 1, 2, 3])
        assert lst < List([2, 3])
        assert lst >= List([0, 1, 2, 3])
        assert lst <= List([2, 3])
        assert lst >= List([1, 2, 3])
        assert lst >= lst
        assert lst <= List([1, 2, 3])
        assert not lst < lst
        assert not lst < List([1, 2, 3])
        assert not lst > lst
        assert not lst > List([1, 2, 3])

    def test_list_functions(self):
        lst = List([1, 2, 3])
        empty = List()

        # Sublist
        assert lst.take(2) == List([1, 2])
        assert lst.drop(1) == List([2, 3])
        assert lst.drop(1) is lst.tail
        assert lst.drop(5) is List()

        # Sort/partition
        assert lst.reversed() == List([3, 2, 1])
        assert lst.partition(lambda x: x % 2 == 0) == (List([1]), List([2, 3]))
        assert empty.partition((X % 2)) == (empty, empty)

        # Mapping
        assert lst.map((X * 2)) == List([2, 4, 6])
        assert lst.map((X * "-")) == List(["-", "--", "---"])
        assert lst.map_bound((X * "-")) == List(["-", "-", "-", "-", "-", "-"])

    def test_empty_list(self):
        empty = List()
        assert empty is List()

        tests = {len: 0, repr: "List([])"}
        for f, v in tests.items():
            assert f(empty) == v

    def test_empty_list_errors(self):
        empty = List()

        tests = {
            getattr("uncons"): ValueError,
            X[0]: IndexError,
            X[-1]: IndexError,
            X * (-1): ValueError,
        }
        for f, e in tests.items():
            with pytest.raises(e):
                res = f(empty)
                print("result:", res)
