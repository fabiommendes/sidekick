from pathlib import Path
import readme_renderer.rst
import sys
import re

roles_re = re.compile(r":py(?::\w)*:")


def test_readme():
    """
    Verify if readme still works after eliminating :py: roles via transform
    mirrored in setup.py.
    """
    file = Path(__file__).parent.parent / "README.rst"
    src = roles_re.sub("", file.read_text())
    data = readme_renderer.rst.render(src, stream=sys.stderr)
    assert data is not None
