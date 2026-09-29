from pathlib import Path
from invoke import task
import sys

sub_package = "properties"

PACKAGES = [
    # Core libs
    ("core", ["properties", "core", "functions", "proxy", "seq"]),
    # Data types
    ("data", ["tree", "collections", "types"]),
    # Extra
    ("extra", ["api", "beta", "experimental", "extra", "hypothesis", "ideas"]),
]


@task
def develop(ctx, install=False, dry_run=False):
    """
    Install all sidekick libraries.
    """
    cmd = "install" if install else "develop"
    
    run = print if dry_run else ctx.run
    for _, grp in PACKAGES:
        for lib in grp:
            run(f"cd sidekick-{lib} && {sys.executable} setup.py {cmd}")


@task
def uninstall(ctx, dry_run=False):
    """
    Install all sidekick libraries.
    """
    run = print if dry_run else ctx.run
    for _, grp in PACKAGES:
        for lib in grp:
            run(f"pip uninstall sidekick-{lib} --yes")


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
    return ctx.run(
        f"python -c 'import sidekick.{sub_package}'"
        f" && pytest tests/ --cov --cov-report=xml {flags}",
        pty=True,
    )


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
    ctx.run("flake8 sidekick/")
    ctx.run("mypy sidekick/")


@task
def ci(ctx, dry_run=False):
    """
    Full pipeline performed by CI runner.
    """
    conf = Path(".github/workflows/pythonpackage.yml").read_text()
    _, _, src = conf.partition("Run CI")
    _, _, src = src.partition("|")
    src, _, _ = src.partition("- name: ")
    cmds = [ln[8:] for ln in src.splitlines() if ln.strip()]

    if dry_run:
        print("Dry run:")
        print("\n".join(cmds))
        return

    print("Running commands:")
    for cmd in cmds:
        ctx.run(cmd, pty=True)
