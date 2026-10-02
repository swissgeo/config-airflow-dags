import logging

import pyarrow as pa
from pyarrow import csv

logger = logging.getLogger("pipeline_toolset")


# Intentionally going with a limited set of options here. If needed, we shall add more
# (or tell the data providers to provide their data in a specific style?)
# See
#   https://arrow.apache.org/docs/python/generated/pyarrow.csv.ReadOptions.html#pyarrow.csv.ReadOptions
#   https://arrow.apache.org/docs/python/generated/pyarrow.csv.ParseOptions.html#pyarrow.csv.ParseOptions
#   https://arrow.apache.org/docs/python/generated/pyarrow.csv.ConvertOptions.html#pyarrow.csv.ConvertOptions
# for more information on what's possible
def parse_csv(file_path: str, encoding: str, delimiter: str, quote_char: str = '"') -> pa.Table:
    """
    Parse a CSV file into a PyArrow Table.

    Args:
        file_path: str Path to file
        encoding: str Encoding of the CSV file (utf-8, latin-1 etc.)
        delimiter: str Delimiter used in the CSV file
        quote_char: str Quote character used in the CSV file (default: ")

    Returns:
        pa.Table: The parsed CSV data as a PyArrow Table.
    """
    logger.info("Parsing CSV")
    logger.debug(
        "Using encoding %s, delimiter %s and quote_char %s",
        encoding,
        delimiter,
        quote_char,
    )

    return csv.read_csv(
        file_path,
        read_options=csv.ReadOptions(encoding=encoding),
        parse_options=csv.ParseOptions(delimiter=delimiter, quote_char=quote_char),
    )
