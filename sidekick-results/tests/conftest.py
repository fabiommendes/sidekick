import pytest
from sidekick.results import Nothing


@pytest.fixture(autouse=True)
def sidekick_namespace(doctest_namespace: dict):
    from sidekick.results import Ok, Err, Result, safe  # noqa: F401
    from sidekick.lambdas import X, Y, M, F  # noqa: F401
    from dataclasses import dataclass  # noqa: F401
    import operator as op  # noqa: F401

    def anyfunc(*args, **kwargs):
        return None

    ns = locals()
    ns["doctest_namespace"]
    doctest_namespace.update(ns)
    doctest_namespace.update(
        do_something=anyfunc,
        do_something_else=anyfunc,
        result=Ok(42),
    )


@pytest.fixture
def null():
    return Nothing
