from sidekick.deferred import Deferred, Proxy


class Foo:
    def __init__(self):
        self.attr = 42


class TestDeferred:
    def test_deferred_object_is_created_on_touch(self):
        obj = Deferred(Foo)
        assert obj.attr == 42