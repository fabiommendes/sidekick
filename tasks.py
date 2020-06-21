from invoke import task


@task
def test(ctx, all=False):
    """
    Run tests.
    """
    if all:
        doctest(ctx)
    ctx.run("pytest tests/", pty=True)


@task
def docs(ctx, clear=False, strict=False, auto=False):
    """
    Build documentation.
    """
    suffix = " -W" if strict else ""
    if clear:
        ctx.run("rm -rf build/docs/")
    if auto:
        ctx.run("sphinx-autobuild docs/ build/docs/ -n" + suffix, pty=True)
    else:
        ctx.run("sphinx-build docs/ build/docs/ -n" + suffix, pty=True)


@task
def doctest(ctx):
    """
    Run sphinx doc tests.
    """
    ctx.run("rm -rf docs/_build/")
    ctx.run("cd docs && make doctest")


@task
def check_style(ctx):
    """
    Check code style issues.
    """
    ctx.run("black . --check")
    ctx.run("flake8 sidekick")
