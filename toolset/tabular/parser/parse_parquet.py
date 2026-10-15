import logging

import pyarrow as pa
import pyarrow.parquet as pq

logger = logging.getLogger("pipeline_toolset")


def parse_parquet(file_path: str) -> pa.Table:
    """Parse a Parquet file into a pyarrow Table

    Args:
        file_path (str): Path to the Parquet file.

    Returns:
        pa.Table: The parsed Parquet table as pyarrow Table
    """
    logger.info("Reading Parquet file")

    return pq.read_table(file_path)
