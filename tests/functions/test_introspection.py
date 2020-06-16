from inspect import Signature, _empty

import sidekick.api as sk


class TestIntrospection:
    def test_arity(self):
        assert sk.arity(lambda x, y: None) == 2

    def test_signature(self):
        sig: Signature = sk.signature(lambda x, y: None)
        assert sig.return_annotation == sig.empty
        assert list(sig.parameters) == ["x", "y"]

    def test_stub(self):
        def add(x: float, y: float) -> float:
            return x + y

        stub = sk.stub(add)
        assert str(stub) == "def add(x: float, y: float) -> float: ..."
