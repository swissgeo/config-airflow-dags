import logging
from collections.abc import Callable
from typing import Any

import pyarrow as pa

logger = logging.getLogger("pipeline_toolset")


def add_column(
    arrow_table: pa.Table,
    column_name: str,
    column_type: pa.DataType,
    value_callback: Callable | None = None,
    column_position: int | None = None,
    static_value: Any | None = None,
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
        static_value: Optional static value to use for all rows. If None, nulls will be used.

    Returns:
        A new pa.Table with the added column.
    """

    if not isinstance(arrow_table, pa.Table):
        raise TypeError(f"Data must be a pyarrow.Table, got {type(arrow_table).__name__}")

    if column_name in arrow_table.column_names:
        raise ValueError(f"Column '{column_name}' already exists in {arrow_table.column_names}")

    if static_value is not None and value_callback is not None:
        raise ValueError("Provide either `value` or `value_callback`, not both")

    n = arrow_table.num_rows
    if value_callback is not None:
        values = pa.array(
            [value_callback(row) for row in arrow_table.to_pylist()],
            type=column_type,
        )
    elif static_value is None:
        values = pa.nulls(n, type=column_type)
    else:
        # constant: one scalar repeated, no per-row Python work
        values = pa.repeat(pa.scalar(static_value, type=column_type), n)

    field = pa.field(column_name, column_type)

    column_position = (
        column_position if column_position is not None else len(arrow_table.column_names)
    )

    logger.info("Appending new column %s at position %s", column_name, column_position)
    return arrow_table.add_column(column_position, field, values)
