from pathlib import Path
import re
from setuptools import setup, find_namespace_packages
from itertools import chain

# Package properties
sub_package = "app"
min_python = (3, 6)
python_requires = ">=3.6"
extras_require = {
    "gcf": ["sidekick.core"],
    "cli": ["typer"],
    "fast-api": ["fast-api"],
}
extras_require["all"] = list(set(chain(*extras_require.values())))

# Package properties
version_re = re.compile(r"""__version__\s+=\s+['"]([^'"]+)['"]""")
roles_re = re.compile(r":py(?::\w)*:")
package_dir = Path("sidekick") / sub_package
read_version = lambda: version_re.findall((package_dir / "__init__.py").read_text())[0]
setup(
    name=f"sidekick-{sub_package}",
    url="https://sidekick.readthedocs.io/",
    author="Fábio Macêdo Mendes",
    author_email="fabiomacedomendes@gmail.com",
    description="Sidekick micro framework to declare simple apps around functions.",
    classifiers=[
        "Intended Audience :: Developers",
        "Development Status :: 5 - Production/Stable",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        *(f"Programming Language :: Python :: 3.{i}" for i in range(min_python[1], 11)),
        "Topic :: Software Development :: Libraries",
        "Topic :: Utilities",
        "Typing :: Typed",
    ],
    python_requires=f">={min_python[0]}.{min_python[1]}",
    package_data={f"sidekick.{sub_package}": ["py.typed", "*.pyi"]},
    platforms=["any"],
    license="MIT License",
    long_description=roles_re.sub("", Path("README.rst").read_text()),
    version=read_version(),
    packages=find_namespace_packages(include=["sidekick.*"]),
    install_requires=[],
    extras_require=extras_require,
    requires=["sidekick.proxy"],
)
