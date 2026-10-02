"""
Library for all parser nodes

This module provides the functionality to parse various data formats

Base Definition:
- Input: string representing the id, path, or name of the resource to import
- Output: a file object (as defined in Python's glossary)
"""

from .parse_csv import parse_csv
from .parse_parquet import parse_parquet

__all__ = [
    "parse_csv",
    "parse_parquet",
]
