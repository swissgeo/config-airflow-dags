import pyarrow as pa


def rename_column(table: pa.Table, old_name: str, new_name: str) -> pa.Table:
    """Rename a column in a PyArrow Table."""
    if old_name not in table.column_names:
        raise ValueError(f"Column '{old_name}' not found in table")

    return table.rename_columns(
        [new_name if col == old_name else col for col in table.column_names]
    )
