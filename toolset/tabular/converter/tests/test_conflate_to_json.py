import json

import pyarrow as pa
import pytest

from tabular.converter import conflate_to_json


@pytest.fixture
def table():
    return pa.Table.from_pydict(
        {
            "point_type_de": ["Station"],
            "point_type_fr": ["Station"],
            "point_type_it": ["Stazione"],
            "point_type_en": ["Station"],
        }
    )


def test_conflate_to_json_builds_json_objects(table):
    result = conflate_to_json(
        table,
        ["point_type_de", "point_type_fr", "point_type_it", "point_type_en"],
        "point_type",
    )

    parsed = [json.loads(v) for v in result.column("point_type").to_pylist()]
    assert parsed == [
        {
            "point_type_de": "Station",
            "point_type_fr": "Station",
            "point_type_it": "Stazione",
            "point_type_en": "Station",
        }
    ]


def test_conflate_to_json_column_type_is_json(table):
    result = conflate_to_json(
        table,
        ["point_type_de", "point_type_fr", "point_type_it", "point_type_en"],
        "point_type",
    )

    assert result.schema.field("point_type").type == pa.json_(pa.string())


def test_conflate_to_json_keeps_original_columns(table):
    result = conflate_to_json(
        table,
        ["point_type_de"],
        "point_type",
    )

    assert result.column_names == [
        "point_type_de",
        "point_type_fr",
        "point_type_it",
        "point_type_en",
        "point_type",
    ]
    assert result.column("point_type_de").to_pylist() == ["Station"]
    assert result.column("point_type_fr").to_pylist() == ["Station"]
    assert result.column("point_type_it").to_pylist() == ["Stazione"]
    assert result.column("point_type_en").to_pylist() == ["Station"]


def test_conflate_to_json_preserves_nulls():
    data = pa.Table.from_pydict({"point_type_de": ["Station", None]})

    result = conflate_to_json(data, ["point_type_de"], "point_type")

    parsed = [json.loads(v) for v in result.column("point_type").to_pylist()]
    assert parsed == [{"point_type_de": "Station"}, {"point_type_de": None}]


def test_conflate_to_json_empty_table():
    data = pa.Table.from_pydict({"point_type_de": pa.array([], type=pa.string())})

    result = conflate_to_json(data, ["point_type_de"], "point_type")

    assert result.num_rows == 0
    assert "point_type" in result.column_names


def test_conflate_to_json_raises_on_missing_column(table):
    with pytest.raises(KeyError):
        conflate_to_json(table, ["point_type_de", "missing"], "point_type")
