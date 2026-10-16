import logging

import pyarrow as pa

logger = logging.getLogger("pipeline_toolset")


def drop_columns(arrow_table: pa.Table, columns: list[str]) -> pa.Table:
    """Drop the specified columns from the table.

    Args:
        arrow_table (pa.Table): The input table.
        columns (list[str]): The names of the columns to drop.

    Returns:
        pa.Table: The table with the specified columns dropped.
    """
    logger.info("Going to drop columns: %s", columns)

    return arrow_table.drop_columns(columns)
