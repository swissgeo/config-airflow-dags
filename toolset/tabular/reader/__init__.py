"""
Library for all reader nodes

These nodes have to be the first in a series of nodes. This means they wont get
the dataframe (pa.Table) passed in, in comparison with all the other nodes.

Base Definition:
- Input: A file object (file-like object)
- Output: A PyArrow Table
"""

from .download_from_s3 import download_from_s3
from .read_from_s3tables import read_from_s3tables

__all__ = ["download_from_s3", "read_from_s3tables"]
