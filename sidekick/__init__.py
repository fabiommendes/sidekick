"""
A companion library that enhance your functional superpowers.
"""
#
# CODE BASE OVERVIEW
#
# All modules starting with a leading underscore are meant to for internal use.
# Sometimes they contain non-public implementations of functions and types that
# may be later be exposed either by wrapping in a sidekick fn() or generator()
# functions or are re-exported from a proper location.
#
__author__ = "Fábio Macêdo Mendes"
__version__ = "0.8.2"

# flake8: noqa
from .api import *
