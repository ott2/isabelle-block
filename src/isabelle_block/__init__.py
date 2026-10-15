"""Mechanical block surgery on Isabelle theory sources.

The command-line tool is the product; `isabelle_block.cli` is its
implementation and has no public library surface yet.
"""
from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("isabelle-block")
except PackageNotFoundError:  # running from a source tree, not installed
    __version__ = "0+unknown"
