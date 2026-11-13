# ruff: noqa: E731 PT011

import pyarrow as pa
import pyarrow.compute as pc
import pytest

from swissgeo_toolset.tabular.converter import add_column


def test_add_column_adds_column_correctly():
    data = pa.Table.from_pydict({"a": [1, 2, 3]})

    func = lambda x: pc.multiply(x["a"], 2)  # ty: ignore[unresolved-attribute]

    result = add_column(data, "b", pa.int64(), func)

    assert result.column("b").to_pylist() == [2, 4, 6]


def test_add_column_at_position():
    data = pa.Table.from_pydict({"a": [1, 2, 3]})

    func = lambda x: pc.multiply(x["a"], 2)  # ty: ignore[unresolved-attribute]

    result = add_column(data, "b", pa.int64(), func, column_position=0)

    assert result.column_names == ["b", "a"]


def test_add_column_adds_column_wrong_type():
    data = pa.Table.from_pydict({"a": [1, 2, 3]})

    func = lambda x: pc.multiply(x["a"], 2)  # ty: ignore[unresolved-attribute]

    with pytest.raises(pa.lib.ArrowInvalid) as exc:
        add_column(data, "b", pa.string(), func)

    msg = str(exc.value)
    assert "Field type did not match data type" in msg


def test_add_column_raises_when_column_already_exists():
    data = pa.Table.from_pydict({"a": [1, 2, 3]})

    func = lambda x: pc.multiply(x["a"], 2)  # ty: ignore[unresolved-attribute]

    with pytest.raises(ValueError) as exc:
        add_column(data, "a", pa.int64(), func)
    assert "already exists" in str(exc.value)


def test_add_column_wrong_input():
    data = {"a": [1, 2, 3]}

    func = lambda x: pc.multiply(x["a"], 2)  # ty: ignore[unresolved-attribute]

    with pytest.raises(TypeError):
        add_column(data, "b", pa.int64(), func)


def test_add_column_without_callback():
    data = pa.Table.from_pydict({"a": [1, 2, 3]})

    result = add_column(data, "b", pa.int64())

    assert result.column("b").to_pylist() == [None, None, None]


def test_add_column_with_static_value():
    data = pa.Table.from_pydict({"a": [1, 2, 3]})

    result = add_column(data, "b", pa.int64(), static_value=42)

    assert result.column("b").to_pylist() == [42, 42, 42]
