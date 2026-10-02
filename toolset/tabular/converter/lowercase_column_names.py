import logging
from collections import Counter

import pyarrow as pa

logger = logging.getLogger(__name__)


def lowercase_column_names(data: pa.Table) -> pa.Table:
    """Lowercase all column names in a PyArrow Table.

    Raises a ValueError if column names are not unique after lowercasing.

    Args:
        data (pa.Table): The input PyArrow Table.

    Returns:
        pa.Table: The Table with lowercase column names.
    """
    new_columns = [col.lower() for col in data.column_names]

    logger.info("Lowercasing column names")
    logger.debug("Column renaming: %s -> %s", data.column_names, new_columns)

    new_data = data.rename_columns(new_columns)

    # pyarrow allows for two columns to have the same name
    # so let's check for it explicitly to avoid errors down the pipeline
    duplicates = [x for x, n in Counter(new_data.column_names).items() if n > 1]

    if duplicates:
        raise ValueError(f"Column names are not unique: {duplicates}")

    return new_data
