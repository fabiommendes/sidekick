from types import SimpleNamespace

import pytest
import sidekick.properties as mod
import sidekick.properties.properties as impl

try:
    from sidekick.core import placeholder as _
except ImportError:
    _ = None


class TestLazyDecorator:
    @pytest.fixture(scope="class")
    def cls(self):
        class Cls(object):
            @mod.lazy
            def c(self):
                return self.a + self.b

            def __init__(self, a, b):
                self.a = a
                self.b = b

        return Cls

    def test_lazy_attribute_is_cached(self, cls):
        a = cls("foo", "bar")
        other = "foo" + "bar"
        assert a.c == "foobar"
        assert a.c is a.c
        assert a.c is not other

    def test_lazy_attribute_is_writable(self, cls):
        a = cls(1, 2)
        a.c = 0
        assert a.c == 0

    def test_lazy_class_accessor(self, cls):
        assert cls.c.is_lazy
        assert cls.c.is_property
        assert cls.c.is_mutable
        assert isinstance(cls.c, impl._Lazy)

    def test_descriptor_can_find_name_its_name(self, cls):
        assert cls.c._init_name(cls) == "c"
        assert impl.find_descriptor_name(cls.c, cls) == "c"
        assert impl.find_descriptor_owner(cls.c, cls) is cls

    def test_cannot_find_descriptor_name_of_wrong_class(self, cls):
        with pytest.raises(RuntimeError):
            impl.find_descriptor_name(cls.c, object)

        with pytest.raises(RuntimeError):
            impl.find_descriptor_owner(cls.c, object)


class TestLazyShared:
    @pytest.fixture(scope="class")
    def cls(self):
        class Cls(object):
            a = 1.0
            b = 2.0

            @mod.lazy(shared=True)
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
            x = mod.delegate_to("data", mutable=True)
            y = mod.delegate_to("data.w", mutable=True)
            z = mod.delegate_to("data")
            w_double_ro = mod.delegate_to("data.w", transform=lambda x: 2.0 * x)
            w_double_rw = mod.delegate_to(
                "data.w", transform=lambda x: 2.0 * x, prepare=lambda x: x / 2
            )

            def __init__(self, data):
                self.data = data

        return cls

    @pytest.fixture
    def data(self):
        return SimpleNamespace(x=1, y=2, z=3, w=4)

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
        assert isinstance(cls.x, impl._MutableDelegate)

    def test_delegate_transforms(self, obj, cls):
        assert not cls.w_double_ro.is_mutable
        assert cls.w_double_rw.is_mutable
        assert obj.w_double_ro == obj.w_double_rw == obj.y * 2.0
        
        obj.w_double_rw = 4.0 * obj.y
        assert obj.w_double_rw == obj.y * 2.0

class TestAliasDecorator:
    @pytest.fixture(scope="class")
    def double(self):
        return lambda x: 2 * x

    @pytest.fixture(scope="class")
    def half(self):
        return lambda x: x / 2

    @pytest.fixture(scope="class")
    def cls(self, double, half):
        class Class(object):
            x = 1
            y = mod.alias("x", mutable=True)
            z = mod.alias("x")
            w = mod.alias("x", transform=double, prepare=half)
            k = mod.alias("x", transform=double)

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


@pytest.mark.skipif(_ is None, reason="Tests that uses sidekick API")
class TestQuickLambdaIntegration:
    def test_lazy_works_with_quick_lambdas(self, cls):
        class B(cls):
            d = mod.lazy(_.a + _.b + _.c)

        x = B(1, 2)
        assert x.d == 6


@pytest.mark.skipif(_ is None, reason="Tests that uses sidekick API")
class TestAliasDecoratorUsingPlaceholders(TestAliasDecorator):
    @pytest.fixture(scope="class")
    def double(self):
        return _ * 2

    @pytest.fixture(scope="class")
    def half(self):
        return _ / 2
