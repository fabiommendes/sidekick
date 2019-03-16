import sys

from invoke import run, task


@task
def configure(ctx):
    """
    Instructions for preparing package for development.
    """

    run("%s -m pip install .[dev] -r requirements.txt" % sys.executable)


@task
def docs(ctx, watch=False):
    """
    Instructions for preparing package for development.
    """

    method = 'autobuild' if watch else 'build'
    run(f'sphinx-{method} docs/ build/docs/')
