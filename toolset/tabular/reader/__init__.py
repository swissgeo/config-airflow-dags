"""
Library for all reader nodes

These nodes don't have an input as the other tools in the sense that data is provided
Instead, they get a params definiting where to read data from.

Base Definition:
- Output: A PyArrow Table
"""

from .read_from_s3tables import read_from_s3tables

__all__ = ["read_from_s3tables"]
