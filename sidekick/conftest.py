import pytest

pytestmark = pytest.mark.slow()


@pytest.fixture(autouse=True)
def add_sidekick_ns(doctest_namespace):
    import sidekick as sk
    from sidekick.api import _, fn
    from sidekick import op, pred, L, N, X, Y

    doctest_namespace.update(**locals())
