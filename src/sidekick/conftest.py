import pytest


@pytest.fixture(autouse=True)
def add_sidekick_ns(doctest_namespace):
    import sidekick as sk
    from sidekick import placeholder as _, op, fn, L, N

    doctest_namespace.update(_=_, sk=sk, op=op, fn=fn, L=L, N=N)
