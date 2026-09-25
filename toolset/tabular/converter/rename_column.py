import logging

import pyarrow as pa

logger = logging.getLogger("pipeline_toolset")


def rename_column(table: pa.Table, old_name: str, new_name: str) -> pa.Table:
    """Rename a column in a PyArrow Table

    Args:
        table: The PyArrow Table to rename the column in
        old_name: The name of the column to rename
        new_name: The new name for the column
    Returns:
        The PyArrow Table with the column renamed
    """
    if old_name not in table.column_names:
        raise KeyError(f"Column '{old_name}' not found in table")

    if new_name in table.column_names:
        # although technically pyarrow would allow multiple columns with the same name,
        # we raise an error to prevent confusion and errors further down the chain
        raise KeyError(f"Column '{new_name}' already exists in table")

    logger.info("Renaming column '%s' to '%s'", old_name, new_name)

    return table.rename_columns(
        [new_name if col == old_name else col for col in table.column_names]
    )
