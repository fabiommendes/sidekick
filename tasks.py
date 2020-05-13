from invoke import task


@task
def test(ctx):
    """
    Run tests.
    """
    ctx.run("pytest tests/")

@task
def check_style(ctx):
    """
    Run tests.
    """
    ctx.run("pytest tests/")