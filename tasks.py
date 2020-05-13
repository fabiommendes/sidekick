from invoke import task


@task
def test(ctx):
    """
    Run tests.
    """
    ctx.run("pytest tests/")


@task
def docs(ctx, strict=False):
    """
    Build documentation.
    """
    suffix = " -W" if strict else ""
    ctx.run("sphinx-build docs/ build/docs/ -n" + suffix)


@task
def check_style(ctx):
    """
    Check code style issues.
    """
    ctx.run("black . --check")
    ctx.run("flake8 sidekick")
