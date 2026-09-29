import pytest

import sidekick as sk
from sidekick import zombie, deferred, record
from sidekick.proxy.zombie import Zombie


class TestDeferred:
    @pytest.fixture(scope="class")
    def cls(self):
        class Cls:
            def __init__(self):
                print("initializing...")
                self.attr = 42

        return Cls

    def test_delayed_object_is_created_on_touch(self, cls):
        obj = zombie(cls)
        assert obj.attr == 42
        assert isinstance(obj, cls)

    def test_delayed_starts_as_a_different_class(self, cls):
        obj = zombie(cls)
        assert not isinstance(obj, cls)
        assert type(obj) is Zombie
        assert isinstance(obj, zombie)
        str(obj)
        assert isinstance(obj, cls)

    def test_deferred_object_is_created_on_touch(self, cls):
        obj = deferred(cls)
        assert obj.attr == 42

    def test_deferred_preserves_class(self, cls):
        obj = deferred(cls)
        assert isinstance(obj, sk.Proxy)
        str(obj)
        assert isinstance(obj, sk.Proxy)

    def test_delayed_with_result_class(self):
        obj = zombie[record](record, x=1, y=2)
        assert type(obj) == zombie[record]
        assert isinstance(obj, zombie[record])
        assert str(obj) == "record(x=1, y=2)"
        assert type(obj) == record


class TestLazyImport:
    def test_lazy_import(self):
        assert sk.import_later("math").sqrt(4) == 2.0
        assert sk.import_later("math:sqrt")(4) == 2.0
        assert sk.import_later("sidekick.pred").is_zero(0)
        assert sk.import_later("sidekick.pred:is_zero")(0)
