import os
import sys

from invoke import run, task

sys.path.append('src')
os.environ['PYTHONPATH'] = 'src'


@task
def configure(ctx):
    """
    Instructions for preparing package for development.
    """

    run("poetry update")


@task
def docs(ctx, watch=False):
    """
    Instructions for preparing package for development.
    """

    method = 'autobuild' if watch else 'build'
    run(f'sphinx-{method} docs/ build/docs/')
