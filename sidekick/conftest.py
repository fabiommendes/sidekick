import pytest

pytestmark = pytest.mark.slow()


@pytest.fixture(autouse=True)
def add_sidekick_ns(doctest_namespace):
    doctest_namespace.update(**locals())
