"""
Library for all parser nodes

This module provides the functionality to parse various data formats

Base Definition:
- Input: string representing the id, path, or name of the resource to import
- Output: a pa.Table object
"""

from .parse_csv import parse_csv
from .parse_parquet import parse_parquet

__all__ = [
    "parse_csv",
    "parse_parquet",
]
