import logging
import typing

import pyarrow as pa
from pyarrow import csv

logger = logging.getLogger("pipeline_toolset")


def parse_csv(file: typing.IO[bytes], encoding: str, delimiter: str) -> pa.Table:
    """
    Parse a CSV file into a PyArrow Table.

    Args:
        file (io.TextIOWrapper): The CSV file to parse.

    Returns:
        pa.Table: The parsed CSV data as a PyArrow Table.
    """
    logger.info("Parsing CSV file with encoding %s and delimiter %s", encoding, delimiter)

    # https://arrow.apache.org/docs/python/generated/pyarrow.csv.ReadOptions.html#pyarrow.csv.ReadOptions
    # https://arrow.apache.org/docs/python/generated/pyarrow.csv.ParseOptions.html#pyarrow.csv.ParseOptions
    # https://arrow.apache.org/docs/python/generated/pyarrow.csv.ConvertOptions.html#pyarrow.csv.ConvertOptions

    table = csv.read_csv(
        file,
        read_options=csv.ReadOptions(encoding=encoding),
        parse_options=csv.ParseOptions(delimiter=delimiter),
    )

    # TODO consider whether closing the file handle should be done here
    # see https://github.com/swissgeo/config-airflow-dags/pull/3#discussion_r4103483671
    file.close()
    return table
