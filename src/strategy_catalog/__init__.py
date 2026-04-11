"""Neutral strategy catalog reader package.

This package is the new canonical source for reading strategy catalogs from
files. It must not depend on legacy registry launch builders.
"""

from .reader import load_strategy_catalog

__all__ = ["load_strategy_catalog"]
