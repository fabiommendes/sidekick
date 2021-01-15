import pytest
import sidekick.api as sk
import sidekick.hypothesis
from sidekick import op


@pytest.fixture(autouse=True)
def sidekick_namespace(doctest_namespace):
    doctest_namespace.update(
        sk=sk,
        X=sk.X,
        Y=sk.Y,
        M=sk.M,
        F=sk.F,
        op=op,
        st=sidekick.hypothesis,
    )
