from pathlib import Path

import pytest
import sys

import sidekick.api as sk
import sidekick.hypothesis
from sidekick import op

sys.path.append(str(Path(__file__).parent.parent))


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


@pytest.fixture(params=[tuple, lambda: iter(())])
def empty(request):
    return request.param


@pytest.fixture(params=[tuple, lambda: iter(())])
def empty_seq(empty):
    return empty()


@pytest.fixture(params=[True, False])
def nums(request):
    # We create named functions to make it easier to debug later
    if request.param:

        def sequence():
            return range(1, 6)

        return sequence
    else:

        def iterator():
            return iter(range(1, 6))

        return iterator
