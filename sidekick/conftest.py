import pytest

pytestmark = pytest.mark.slow()


@pytest.fixture(autouse=True)
def add_sidekick_ns(doctest_namespace):
    import sidekick as sk
    from sidekick.api import _, fn, X, Y
    from sidekick import op, pred

    doctest_namespace.update(**locals())
