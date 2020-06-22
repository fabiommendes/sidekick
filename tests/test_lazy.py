import pytest

import sidekick as sk
from sidekick import deferred, zombie, lazy, Deferred
from sidekick import placeholder as _, record
from sidekick.lazy.zombie import ZombieTypes
from sidekick.lazy.lazy import (
    find_descriptor_name,
    find_descriptor_owner,
    Delegate,
    Lazy,
)


class TestLazyDecorator:
    @pytest.fixture(scope="class")
    def cls(self):
        class Cls(object):
            @lazy
            def c(self):
                return self.a + self.b

            def __init__(self, a, b):
                self.a = a
                self.b = b

        return Cls

    def test_lazy_attribute_is_cached(self, cls):
        a = cls("foo", "bar")
        assert a.c == "foobar"
        assert a.c is a.c
        assert a.c is not "foobar"

    def test_lazy_attribute_is_writable(self, cls):
        a = cls(1, 2)
        a.c = 0
        assert a.c == 0

    def test_lazy_works_with_quick_lambdas(self, cls):
        class B(cls):
            d = sk.lazy(_.a + _.b + _.c)

        x = B(1, 2)
        assert x.d == 6

    def test_lazy_class_accessor(self, cls):
        assert isinstance(cls.c, Lazy)

    def test_descriptor_can_find_name_its_name(self, cls):
        assert cls.c._init_name(cls) == "c"
        assert find_descriptor_name(cls.c, cls) == "c"
        assert find_descriptor_owner(cls.c, cls) is cls

    def test_cannot_find_descriptor_name_of_wrong_class(self, cls):
        with pytest.raises(RuntimeError):
            find_descriptor_name(cls.c, object)

        with pytest.raises(RuntimeError):
            find_descriptor_owner(cls.c, object)


class TestLazyShared:
    @pytest.fixture(scope="class")
    def cls(self):
        class Cls(object):
            a = 1.0
            b = 2.0

            @sk.lazy(shared=True)
            def c(self):
                return self.a + self.b

        return Cls

    def test_shared_lazy_accessor(self, cls):
        a = cls()
        b = cls()
        assert a.c is b.c
        assert a.c is cls.c


class TestDelegateToDecorator:
    @pytest.fixture(scope="class")
    def cls(self):
        class cls(object):
            x = sk.delegate_to("data")
            y = sk.delegate_to("data", name="w")
            z = sk.delegate_to("data", read_only=True)

            def __init__(self, data):
                self.data = data

        return cls

    @pytest.fixture
    def data(self):
        return sk.namespace(x=1, y=2, z=3, w=4)

    @pytest.fixture
    def obj(self, data, cls):
        return cls(data)

    def test_delegate_to_reads_data(self, obj):
        assert obj.x == 1
        assert obj.y == 4
        assert obj.z == 3

    def test_delegate_to_can_write(self, obj):
        obj.x = 42
        assert obj.x == 42

    def test_delegate_ro_cannot_write(self, obj):
        with pytest.raises(AttributeError):
            obj.z = 42

        assert obj.y == 4
        assert obj.z == 3

    def test_delegate_class_accessor(self, cls):
        assert isinstance(cls.x, Delegate)


class TestAliasDecorator:
    @pytest.fixture(scope="class")
    def cls(self):
        class Class(object):
            x = 1
            y = sk.alias("x", mutable=True)
            z = sk.alias("x")
            w = sk.alias("x", transform=2 * _, prepare=_ / 2)
            k = sk.alias("x", transform=2 * _)

        return Class

    @pytest.fixture
    def obj(self, cls):
        return cls()

    def test_alias_read(self, obj):
        assert obj.x == obj.y
        assert obj.y == obj.z

    def test_alias_write(self, obj):
        obj.y = 42
        assert obj.x == obj.y
        assert obj.x == 42
        assert obj.y == 42

    def test_readonly_cannot_write(self, obj):
        with pytest.raises(AttributeError):
            obj.z = 42

        assert obj.z == obj.x

    def test_transforming_alias(self, obj):
        assert obj.w == obj.x * 2
        obj.w = 4
        assert obj.x == 2.0

    def test_transforming_alias_is_read_only_if_prepare_method_is_not_given(self, obj):
        assert obj.k == obj.x * 2

        with pytest.raises(AttributeError):
            obj.k = 42


class TestLazyImport:
    def test_lazy_import(self):
        assert sk.import_later("math").sqrt(4) == 2.0
        assert sk.import_later("math:sqrt")(4) == 2.0
        assert sk.import_later("sidekick.pred").is_zero(0)
        assert sk.import_later("sidekick.pred:is_zero")(0)


class TestDelayed:
    @pytest.fixture(scope="class")
    def cls(self):
        class Cls:
            def __init__(self):
                self.attr = 42

        return Cls

    def test_delayed_object_is_created_on_touch(self, cls):
        obj = zombie(cls)
        assert obj.attr == 42
        assert isinstance(obj, cls)

    def test_delayed_starts_as_a_different_class(self, cls):
        obj = zombie(cls)
        assert isinstance(obj, ZombieTypes)
        str(obj)
        assert isinstance(obj, cls)

    def test_deferred_object_is_created_on_touch(self, cls):
        obj = deferred(cls)
        assert obj.attr == 42

    def test_deferred_preserves_class(self, cls):
        obj = deferred(cls)
        assert isinstance(obj, Deferred)
        str(obj)
        assert isinstance(obj, Deferred)

    def test_delayed_with_result_class(self):
        obj = zombie[record](record, x=1, y=2)
        assert type(obj) == zombie[record]
        assert isinstance(obj, zombie[record])
        assert str(obj) == "record(x=1, y=2)"
        assert type(obj) == record
