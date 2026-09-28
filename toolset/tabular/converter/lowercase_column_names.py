import logging
from collections import Counter

import pyarrow as pa

logger = logging.getLogger("pipeline_toolset")


def lowercase_column_names(arrow_table: pa.Table) -> pa.Table:
    """Lowercase all column names in a PyArrow Table.

    Raises a ValueError if column names are not unique after lowercasing.

    Args:
        arrow_table (pa.Table): The input PyArrow Table.

    Returns:
        pa.Table: The Table with lowercase column names.
    """
    new_columns = [col.lower() for col in arrow_table.column_names]

    logger.info("Lowercasing column names")
    logger.debug("Column renaming: %s -> %s", arrow_table.column_names, new_columns)

    new_data = arrow_table.rename_columns(new_columns)

    # pyarrow allows for two columns to have the same name
    # so let's check for it explicitly to avoid errors down the pipeline
    duplicates = [x for x, n in Counter(new_data.column_names).items() if n > 1]

    if duplicates:
        raise ValueError(f"Column names are not unique: {duplicates}")

    return new_data
