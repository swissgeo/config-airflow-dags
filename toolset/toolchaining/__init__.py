"""Tools for creating a chain of tools

These tools provide the ability to chain together tools to create a workflow
from a YAML configuration file.

The are meant to be used *outside* of the actual pipeline ingestion; instead
they are supposed to be used to create generalized ingestion tool chains
"""

from .parse_yaml import parse_yaml

__all__ = [
    "parse_yaml",
]
