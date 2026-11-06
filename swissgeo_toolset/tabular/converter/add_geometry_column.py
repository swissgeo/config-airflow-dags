from typing import TypedDict

import pyarrow as pa
import shapely


class GeometryCols(TypedDict):
    east: str
    north: str


def add_geometry_column(
    arrow_table: pa.Table, geometry_cols: GeometryCols, new_column_name: str
) -> pa.Table:
    """Add a new column containing lv95 geoemtry in wkt
    Args:
      arrow_table: The input pyarrow table
        geometry_cols: A dictionary mapping column names to geometry coordinates
        new_column_name: The name of the new column to add
    Returns:
        The input table with the new geometry column added
    """

    if "north" not in geometry_cols or "east" not in geometry_cols:
        raise ValueError("geometry_cols must contain 'north' and 'east'")

    if new_column_name in arrow_table.column_names:
        raise ValueError(f"Column '{new_column_name}' already exists")

    xs = arrow_table[geometry_cols["east"]].to_numpy()
    ys = arrow_table[geometry_cols["north"]].to_numpy()

    wkt = shapely.to_wkt(shapely.points(xs, ys), rounding_precision=-1)

    return arrow_table.append_column(
        pa.field(new_column_name, pa.string()),
        pa.array(wkt, pa.string()),
    )
