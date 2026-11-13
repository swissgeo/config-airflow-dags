import logging
from collections.abc import Callable
from typing import Any

import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.dataset as ds

logger = logging.getLogger("pipeline_toolset")


def add_column(  # noqa: PLR0913, PLR0917
    arrow_table: pa.Table,
    column_name: str,
    column_type: pa.DataType,
    value_callback: pc.Expression | Callable[[pa.Table], pa.Array | pa.ChunkedArray] | None = None,
    static_value: Any | None = None,
    column_position: int | None = None,
) -> pa.Table:
    """Add a new column to a PyArrow Table.

    The new column will be named `column_name` and have type `column_type`.
    The values are determined by exactly one of the following (if none is given,
    the column is filled with nulls):

    - `value_callback` as a callable: called once with the whole table, must return a
      pa.Array or pa.ChunkedArray with one value per row (use `pyarrow.compute`
      functions to keep it vectorized).
    - `value_callback` as a `pc.Expression`: evaluated against the table, e.g.
      `pc.field("a") + pc.field("b")`.
    - `static_value`: a constant used for all rows.

    Args:
        arrow_table: The PyArrow Table to extend.
        column_name: Name of the new column.
        column_type: Data type for the new column.
        value_callback: Optional callable taking the table and returning an array of
                        values, or a pc.Expression.
        column_position: Optional position to insert the column at. If None, the column
                         will be appended to the end.
        static_value: Optional static value to use for all rows. If None, nulls will be
                      used (unless `value_callback` is given).

    Returns:
        A new pa.Table with the added column.
    """

    if not isinstance(arrow_table, pa.Table):
        raise TypeError(f"Data must be a pyarrow.Table, got {type(arrow_table).__name__}")

    if column_name in arrow_table.column_names:
        raise ValueError(f"Column '{column_name}' already exists in {arrow_table.column_names}")

    if static_value is not None and value_callback is not None:
        raise ValueError("Provide either `static_value` or `value_callback`, not both")

    n = arrow_table.num_rows

    if value_callback is not None:
        if isinstance(value_callback, pc.Expression):
            values = ds.dataset(arrow_table).to_table(columns={"v": value_callback})["v"]
        else:
            values = value_callback(arrow_table)

        if len(values) != n:
            raise ValueError(f"value_callback returned {len(values)} values for {n} rows")
    elif static_value is None:
        values = pa.nulls(n, type=column_type)
    else:
        values = pa.repeat(pa.scalar(static_value, type=column_type), n)

    field = pa.field(column_name, column_type)

    column_position = (
        column_position if column_position is not None else len(arrow_table.column_names)
    )

    logger.info("Appending new column %s at position %s", column_name, column_position)
    return arrow_table.add_column(column_position, field, values)
