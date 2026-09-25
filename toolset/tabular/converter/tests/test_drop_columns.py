import pyarrow as pa
import pytest

from tabular.converter import drop_columns


def test_drop_single_column():
    data = pa.Table.from_pydict({"a": [1, 2], "b": [3, 4], "c": [5, 6]})

    result = drop_columns(data, ["b"])

    assert result.column_names == ["a", "c"]
    assert result.column("a").to_pylist() == [1, 2]
    assert result.column("c").to_pylist() == [5, 6]


def test_drop_multiple_columns():
    data = pa.Table.from_pydict({"a": [1], "b": ["x"], "c": [True]})

    result = drop_columns(data, ["a", "c"])

    assert result.column_names == ["b"]
    assert result.column("b").to_pylist() == ["x"]


def test_drop_columns_missing_raises():
    data = pa.Table.from_pydict({"a": [1], "b": [2]})

    with pytest.raises(KeyError):
        drop_columns(data, ["z"])


def test_drop_columns_empty_noop():
    data = pa.Table.from_pydict({"a": [1, 2, 3], "b": [4, 5, 6]})

    result = drop_columns(data, [])

    assert result.equals(data)
