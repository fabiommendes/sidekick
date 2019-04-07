import sys

from setuptools import setup, find_packages

sys.path.append('src')

setup(
    name='sidekick',
    package_dir={'': 'src'},
    packages=[pkg for pkg in find_packages('src') if '.beta' not in pkg],
    setup_requires='setuptools >= 30.3',
    install_requires=['toolz']
)
