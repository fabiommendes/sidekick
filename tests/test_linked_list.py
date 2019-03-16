from sidekick.union.linked_list import List, linklist


class TestLinkedLists:
    def test_can_create_linked_list(self):
        ls = linklist([1, 2])
        assert ls.head == 1
        assert ls.tail.tail == List.Nil

    def test_list_has_size(self):
        assert len(linklist([])) == 0
        assert len(linklist([1])) == 1
        assert len(linklist([1, 2])) == 2

    def test_list_is_iterable(self):
        assert list(linklist([])) == []
        assert list(linklist([1])) == [1]
        assert list(linklist([1, 2])) == [1, 2]

    def test_linked_list_obbeys_sequence_interface(self):
        ll = linklist([1, 2])
        assert ll[0] == 1
        assert ll[1] == 2
        assert ll == linklist([1, 2])

    def test_linked_list_repr(self):
        assert str(linklist([1, 2])) == "linklist([1, 2])"
