from sidekick import List, Nil


class TestLinkedLists:
    def test_can_create_linked_list(self):
        ls = List([1, 2])
        assert ls.head == 1
        assert ls.tail.tail == Nil

    def test_list_size(self):
        assert len(List([])) == 0
        assert len(List([1])) == 1
        assert len(List([1, 2])) == 2

    def test_list_is_iterable(self):
        assert list(List([])) == []
        assert list(List([1])) == [1]
        assert list(List([1, 2])) == [1, 2]

    def test_linked_list_obbeys_sequence_interface(self):
        ll = List([1, 2])
        assert ll[0] == 1
        assert ll[1] == 2
        assert ll == List([1, 2])

    def test_linked_list_repr(self):
        assert str(List([1, 2])) == "List([1, 2])"
