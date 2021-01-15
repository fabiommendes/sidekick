from invoke import task


@task
def test(ctx, all=False, maxfail=None, verbose=False):
    """
    Run tests.
    """
    flags = []
    if all:
        doctest(ctx)
    else:
        flags.extend(["--lf", f"--maxfail={maxfail or 2}"])
    if verbose:
        flags.append("-vv")
    flags = " ".join(flags)
    ctx.run(f"python -c 'import sidekick.api' && pytest tests/ {flags}", pty=True)


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
    ctx.run("pytest tests/ --doctest-modules sidekick/ --doctest-plus", pty=True)
    ctx.run("rm -rf docs/_build/")
    ctx.run("cd docs && make doctest", pty=True)


@task
def check_style(ctx):
    """
    Check code style issues.
    """
    ctx.run("black . --check")
    ctx.run("flake8 sidekick")


@task
def ci(ctx):
    """
    Run code that should be executed in continuous integration.
    """
    test(ctx, all=True)
    docs(ctx, strict=True, clear=True)
    # check_style(ctx)
