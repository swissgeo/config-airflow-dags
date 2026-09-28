import logging

import pyarrow as pa
import pyarrow.compute as pc

logger = logging.getLogger("pipeline_toolset")


def convert_column(
    arrow_table: pa.Table,
    column_name: str,
    converter: pc.Function,
    converter_args: dict | None = None,
) -> pa.Table:
    """Converts a column in the table using pyarrow compute functions

    Args:
        arrow_table (pa.Table): The input table.
        column_name (str): The name of the column to convert.
        converter (pa.compute.Function): The pyarrow compute function to apply to each column value.
        converter_args (dict, optional): The arguments to pass to the converter function. Defaults
                                         to None

    Notes: The timestamps are timezone unaware. Maybe that's enough for the pipeline and they
    have to be tz-aware as soon as they're further converted?

    Returns:
        pa.Table: The table with the converted column.
    """

    if converter_args is None:
        converter_args = {}

    if not isinstance(arrow_table, pa.Table):
        raise TypeError(f"df must be a pyarrow.Table, got {type(arrow_table).__name__}")

    if column_name not in arrow_table.column_names:
        raise ValueError(f"Column '{column_name}' not found in the table")

    column_index = arrow_table.column_names.index(column_name)

    # based on the new_type override the type or use the existing one
    old_type = arrow_table.schema[column_index].type

    logger.info(
        "Applying %s to column '%s' with args %s", converter.__name__, column_name, converter_args
    )
    new_column = converter(arrow_table[column_name], **converter_args)

    logger.info("Column '%s' converted: %s -> %s", column_name, old_type, new_column.type)

    return arrow_table.set_column(column_index, column_name, new_column)
