import json
import logging
import re
from collections.abc import Callable

import pyarrow as pa

logger = logging.getLogger("pipeline_toolset")


def add_column(
    data: pa.Table,
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
        data: The PyArrow Table to extend.
        column_name: Name of the new column.
        column_type: Data type for the new column.
        value_callback: Optional callback taking a dict of row data and returning a value
                       for that row.
        column_position: Optional position to insert the column at. If None, the column
                         will be appended to the end.

    Returns:
        A new pa.Table with the added column.
    """

    if not isinstance(data, pa.Table):
        raise TypeError(f"df must be a pyarrow.Table, got {type(data).__name__}")

    if column_name in data.column_names:
        raise ValueError(
            f"Column '{column_name}' already exists in dataframe columns {list(data.column_names)}"
        )

    if value_callback is None:
        values = [None] * data.num_rows
    else:
        values = []
        existing_columns = data.column_names
        for i in range(data.num_rows):
            row_data = {col: data.column(col)[i].as_py() for col in existing_columns}
            val = value_callback(row_data)
            values.append(val)

    logger.info(f"Going to add values (first 10) {values[0:10]}")

    # the json column type is an extension and is not covered by the type aliases in pyarrow
    # therefore we need to import the extension type directly and call it with the
    # appropriate subtype, extracted from the regex match
    json_column = re.match(r"json\((.*)\)", column_type)
    if json_column:
        logger.info(f"Going to add json column '{column_name}' with type {column_type}")
        try:
            json_type = pa.json_
            json_subtype = getattr(pa, json_column.group(1))
            column_type = json_type(json_subtype())
            logger.info(
                f"Determined json column '{column_name}' with subtype {json_column.group(1)}"
            )

            logger.info(f"Going to convert the values to JSON strings")
            values = pa.array([json.dumps(val) for val in values], type=column_type)
        except AttributeError as e:
            raise ValueError(f"Invalid json subtype: {json_column.groups()}") from e

    # ordinary pyarrow type, it can be used via the type alis
    field = pa.field(column_name, column_type)

    if column_position is not None:
        logger.info(
            f"Going to add column '{column_name}' at position {column_position} with field type {field} with values {values[:10]}"
        )
        return data.add_column(column_position, field, [values])
    else:  # noqa: RET505
        logger.info(
            f"Going to append column '{column_name}' with field type {field} with values {values[:10]}"
        )
        return data.append_column(field, [values])
