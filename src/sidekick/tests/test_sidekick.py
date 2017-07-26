import pytest
import sidekick


def test_project_defines_author_and_version():
    assert hasattr(sidekick, '__author__')
    assert hasattr(sidekick, '__version__')
