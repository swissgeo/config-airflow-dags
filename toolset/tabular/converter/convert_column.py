import logging

import pyarrow as pa
from pyarrow import compute as pc

logger = logging.getLogger("pipeline_toolset")


def convert_column(
    arrow_table: pa.Table,
    column_name: str,
    converter_name: str,
    converter_args: dict | None = None,
) -> pa.Table:
    """Converts a column in the table using pyarrow compute functions

    Args:
        arrow_table (pa.Table): The input table.
        column_name (str): The name of the column to convert.
        converter_name (str): The name of the pyarrow compute function to apply
        converter_args (dict, optional): The arguments to pass to the converter function. Defaults
                                         to None


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

    try:
        converter = getattr(pc, converter_name)
    except AttributeError as e:
        raise ValueError(f"Converter '{converter_name}' not found") from e

    new_column = converter(arrow_table[column_name], **converter_args)

    old_type = arrow_table.schema[column_index].type
    logger.info("Column '%s' converted: %s -> %s", column_name, old_type, new_column.type)

    return arrow_table.set_column(column_index, column_name, new_column)
