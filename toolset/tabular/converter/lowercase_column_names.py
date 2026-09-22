import logging

import pyarrow as pa

logger = logging.getLogger(__name__)


def lowercase_column_names(data: pa.Table) -> pa.Table:
    """Lowercase all column names in a PyArrow Table."""
    new_columns = [col.lower() for col in data.column_names]

    logger.info(f"Lowercasing column names: {data.column_names} -> {new_columns}")

    return data.rename_columns(new_columns)
