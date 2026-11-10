import pyarrow as pa
import pytest

from swissgeo_toolset.tabular.converter.add_geometry_column import add_geometry_column


def test_add_geometry_column_basic():
    table = pa.table(
        {
            "north": [1200000.0, 1200001.25],
            "east": [2600000.0, 2600001.5],
            "label": ["first", "second"],
        }
    )

    result = add_geometry_column(
        table,
        {
            "east": "east",
            "north": "north",
        },
        "geom",
    )

    assert result.column_names == ["north", "east", "label", "geom"]
    assert result.schema.field("geom").type == pa.string()

    assert result["geom"].to_pylist() == [
        "POINT (2600000 1200000)",
        "POINT (2600001.5 1200001.25)",
    ]


def test_add_geometry_column_with_custom_names():
    table = pa.table(
        {
            "point_coordinates_lv95_east": [1.123456789],
            "point_coordinates_lv95_north": [2.987654321],
        }
    )

    result = add_geometry_column(
        table,
        {"north": "point_coordinates_lv95_east", "east": "point_coordinates_lv95_north"},
        "mygeom",
    )

    assert result.column_names == [
        "point_coordinates_lv95_east",
        "point_coordinates_lv95_north",
        "mygeom",
    ]
    assert result["mygeom"].to_pylist() == ["POINT (2.987654321 1.123456789)"]


def test_add_geometry_column_empty_table():
    table = pa.table(
        {
            "north": pa.array([], type=pa.float64()),
            "east": pa.array([], type=pa.float64()),
        }
    )

    result = add_geometry_column(table, {"north": "north", "east": "east"}, "geom")

    assert result.column_names == ["north", "east", "geom"]
    assert result.num_rows == 0
    assert result.schema.field("geom").type == pa.string()
    assert result["geom"].to_pylist() == []
    assert result.drop_columns(["geom"]).equals(table)


def test_add_geometry_wrong_column_names():
    table = pa.table(
        {
            "north": pa.array([], type=pa.float64()),
            "east": pa.array([], type=pa.float64()),
        }
    )

    with pytest.raises(ValueError):  # noqa: PT011
        add_geometry_column(table, {"nrth": "north", "est": "east"}, "geom")  # ty: ignore[missing-typed-dict-key,invalid-argument-type,invalid-key]


def test_add_geometry_column_name_colision():
    table = pa.table(
        {
            "geom": pa.array([], type=pa.string()),
        }
    )

    with pytest.raises(ValueError):  # noqa: PT011
        add_geometry_column(table, {"north": "north", "east": "east"}, "geom")
