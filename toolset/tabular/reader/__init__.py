"""
Library for all reader nodes

These nodes expect expect a file_path as string which they will open
and read into a PyArrow Table.

Base Definition:
- Input: Path to a file
- Output: A PyArrow Table
"""

from .read_from_s3tables import read_from_s3tables

__all__ = ["read_from_s3tables"]
