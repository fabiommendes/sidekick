from keyword import iskeyword

import pytest
from hypothesis import given, strategies as st

from sidekick.hypothesis import atoms, identifiers, kwargs

pytestmark = pytest.mark.slow()


class TestBaseStrategies:
    @given(atoms(finite=True))
    def test_valid_atom(self, x):
        assert x == x

    @given(identifiers())
    def test_identifier(self, name):
        assert not iskeyword(name)
        assert name.isidentifier()

    @given(kwargs(st.integers()))
    def test_kwargs(self, args):
        assert not any(iskeyword(key) for key in args)
        assert all(key.isidentifier() for key in args)
        assert all(isinstance(v, int) for v in args.values())
