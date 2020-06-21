from sidekick import misc


class TestLazyList:
    dic_type = misc.LazyList

    def test_create_lazy_list(self):
        lst = misc.LazyList(range(4))

        assert lst.is_lazy
        assert lst.can_be_infinite
        assert lst == [0, 1, 2, 3]

    def test_lazy_list_manipulate_end(self):
        lst = misc.LazyList(range(4))
        lst.append(4)
        lst.extend((5, 6))

        assert lst.pop() == 6
        assert lst.is_lazy
        assert lst.can_be_infinite

        lst.consume_until(5)
        assert not lst.is_lazy
        assert not lst.can_be_infinite
        assert lst == [0, 1, 2, 3, 4, 5]
