import logging
from collections.abc import Callable

import pyarrow as pa

logger = logging.getLogger("pipeline_toolset")


def add_column(
    arrow_table: pa.Table,
    column_name: str,
    column_type: pa.DataType,
    value_callback: Callable | None = None,
    column_position: int | None = None,
) -> pa.Table:
    """Add a new column to a PyArrow Table.

    The new column will be named `column_name` and have type `column_type`.
    If `value_callback` is provided, it will be called for each row with a dict of
    the row's data (mapping column name to value) and its return value will be used
    as the corresponding cell in the new column. If `value_callback` is None, nulls
    will be used for all rows.

    Args:
        arrow_table: The PyArrow Table to extend.
        column_name: Name of the new column.
        column_type: Data type for the new column.
        value_callback: Optional callback taking a dict of row data and returning a value
                       for that row.
        column_position: Optional position to insert the column at. If None, the column
                         will be appended to the end.

    Returns:
        A new pa.Table with the added column.
    """

    if not isinstance(arrow_table, pa.Table):
        raise TypeError(f"Data must be a pyarrow.Table, got {type(arrow_table).__name__}")

    if column_name in arrow_table.column_names:
        raise ValueError(
            f"Column '{column_name}' already exists in dataframe columns "
            f"{list(arrow_table.column_names)}"
        )

    if value_callback is None:
        values = pa.nulls(arrow_table.num_rows, type=column_type)
    else:
        values = pa.array(
            [
                value_callback(row)
                for batch in arrow_table.to_batches()
                for row in batch.to_pylist()
            ],
            type=column_type,
        )

    # ordinary pyarrow type, it can be used via the type alis
    field = pa.field(column_name, column_type)

    if column_position is not None:
        logger.info("Adding new column %s", column_name)
        logger.debug(
            "New column '%s' at position %s with field type %s with values %s",
            column_name,
            column_position,
            field,
            values[:10],
        )
        return arrow_table.add_column(column_position, field, values)
    else:  # noqa: RET505
        logger.info("Appending new column %s", column_name)
        logger.debug(
            "New column '%s' with field type %s with values %s",
            column_name,
            field,
            values[:10],
        )
        return arrow_table.append_column(field, values)
