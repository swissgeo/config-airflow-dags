"""
Library for all writer nodes

This module provides functions to write resources from a PyArrow table to various destinations.

Base Definition:
- Input: pyarrow.Table
- Output: pyarrow.Table passed through
"""

from .write_to_postgres import write_to_postgres
from .write_to_s3tables import WriteToS3TablesError, write_to_s3tables

__all__ = [
    "WriteToS3TablesError",
    "write_to_postgres",
    "write_to_s3tables",
]
