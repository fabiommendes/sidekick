import pytest


@pytest.fixture(autouse=True)
def add_sidekick_ns(doctest_namespace):
    import sidekick as sk
    from sidekick import placeholder as _, op, fn, pred, L, N, X, Y

    doctest_namespace.update(**locals())
