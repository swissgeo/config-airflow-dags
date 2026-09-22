import json
import logging

import pyarrow as pa

logger = logging.getLogger("pipeline_toolset")


def conflate_to_json(data: pa.Table, column_names: list[str], new_column_name: str) -> pa.Table:
    """Conflate the specified columns into a single appended JSON column.

    Each row becomes a JSON object mapping column names to row values.

    Raises:
        KeyError: if any of `column_names` is missing from `data`.
    """
    logger.info(f"Conflating columns {column_names} to JSON column {new_column_name}")

    rows = data.select(column_names).to_pylist()
    json_array = pa.array([json.dumps(row) for row in rows], type=pa.json_(pa.string()))

    return data.append_column(new_column_name, json_array)
