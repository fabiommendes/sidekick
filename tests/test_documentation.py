import os

import manuel.codeblock
import manuel.doctest
import manuel.ignore
import manuel.testing
import pytest


def make_manuel_suite(ns):
    """
    Prepare Manuel test suite.

    Test functions are injected in the given namespace.
    """

    # Wrap function so pytest does not expect an spurious "self" fixture.
    def _wrapped(func, name):
        def wrapped():
            return func()

        wrapped.__name__ = name
        return wrapped

    # Collect documentation files
    cd = os.path.dirname
    path = cd(cd(__file__))
    doc_path = os.path.join(path, "docs")
    lib_path = os.path.join(doc_path, "lib")
    types_path = os.path.join(doc_path, "types")
    readme = os.path.join(path, "README.rst")
    files = [
        *(os.path.join(doc_path, f) for f in os.listdir(doc_path)),
        *(os.path.join(lib_path, f) for f in os.listdir(lib_path)),
        # *(os.path.join(types_path, f) for f in os.listdir(types_path)),
    ]
    files = [f for f in files if f.endswith(".rst") or f.endswith(".txt")]
    files.append(readme)

    # Create manuel suite
    m = manuel.ignore.Manuel()
    m += manuel.doctest.Manuel()
    m += manuel.codeblock.Manuel()

    # Copy tests from the suite to the global namespace
    suite = manuel.testing.TestSuite(m, *files)
    for i, test in enumerate(suite):
        name = "test_doc_%s" % i
        ns[name] = pytest.mark.documentation(_wrapped(test.runTest, name))
    return suite


make_manuel_suite(globals())
