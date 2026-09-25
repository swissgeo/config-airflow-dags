# ruff: noqa: E731 PT011

import pyarrow as pa
import pytest

from tabular.converter import add_column


def test_add_column_adds_column_correctly():
    data = pa.Table.from_pydict({"a": [1, 2, 3]})

    func = lambda x: x["a"] * 2

    result = add_column(data, "b", pa.int64(), func)

    assert result.column("b").to_pylist() == [2, 4, 6]


def test_add_column_adds_column_wrong_type():
    data = pa.Table.from_pydict({"a": [1, 2, 3]})

    func = lambda x: x["a"] * 2

    with pytest.raises(ValueError) as exc:
        add_column(data, "b", pa.string(), func)

    msg = str(exc.value)
    assert "Field type did not match data type" in msg


def test_add_column_raises_when_column_already_exists():
    data = pa.Table.from_pydict({"a": [1, 2, 3]})

    func = lambda x: x["a"] * 2

    with pytest.raises(ValueError) as exc:
        add_column(data, "a", pa.int64(), func)
    assert "already exists" in str(exc.value)
