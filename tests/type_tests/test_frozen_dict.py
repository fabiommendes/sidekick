import pytest

from sidekick import misc


class TestFrozenDict:
    dic_type = misc.FrozenDict

    def test_can_be_key_on_dictionary(self):
        d1 = misc.FrozenDict({"foo": "bar", "bar": "foo"})
        d2 = misc.FrozenDict({"bar": "foo", "foo": "bar"})
        dic = {d1: "hello"}
        assert d1 == d2
        assert dic[d1] == "hello"
        assert dic[d2] == "hello"

    def test_cannot_hash_with_mutable_values(self):
        d1 = misc.FrozenDict({"key": []})
        with pytest.raises(TypeError):
            hash(d1)

    def test_cannot_add_or_delete_key(self):
        d1 = self.dic_type({"foo": "bar", "bar": "foo"})

        with pytest.raises(KeyError):
            d1["ham"] = "spam"

        with pytest.raises(KeyError):
            d1.setdefault("ham", "spam")

        with pytest.raises(KeyError):
            d1.update(ham="spam")


class TestFrozenKeyDict:
    dic_type = misc.FrozenKeyDict
    test_cannot_add_or_delete_key = TestFrozenDict.test_cannot_add_or_delete_key

    def test_can_change_frozen_key_dict(self):
        d1 = misc.FrozenKeyDict({"foo": "bar", "bar": "foo"})
        assert d1 == {"foo": "bar", "bar": "foo"}
        assert d1.setdefault("foo") == "bar"

        d1.update(foo="baz")
        assert d1 == {"foo": "baz", "bar": "foo"}

        d1["bar"] = "foobar"
        assert d1 == {"foo": "baz", "bar": "foobar"}
