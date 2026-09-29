from pathlib import Path

REPO = Path(__file__).parent.parent


def test_readme():
    """
    We override function's __doc__ with the README to make it testable by
    the standard --doctest-modules flag in pytest
    """
    # This function does nothing


test_readme.__doc__ = (REPO / "README.rst").read_text()
