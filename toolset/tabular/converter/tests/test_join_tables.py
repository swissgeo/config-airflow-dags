import pyarrow as pa
import pytest

from tabular.converter import join_tables


def test_join_tables():
    table1 = pa.table({"a": [1, 2, 3], "b": [10, 20, 30]})
    table2 = pa.table({"a": [1, 2, 3], "c": [100, 200, 300]})
    result = join_tables(table1, table2, ["a"], "inner")

    assert result == pa.table({"a": [1, 2, 3], "b": [10, 20, 30], "c": [100, 200, 300]})


def test_join_tables_duplicate_columns():
    table1 = pa.table({"a": [1, 2, 3], "b": [10, 20, 30]})
    table2 = pa.table({"a": [1, 2, 3], "b": [100, 200, 300]})

    with pytest.raises(ValueError):  # noqa: PT011
        join_tables(table1, table2, ["a"], "inner")


def test_join_tables_key_mismatch():
    table1 = pa.table({"a": [1, 2, 3]})
    table2 = pa.table({"b": [10, 20, 30]})

    with pytest.raises(KeyError):
        join_tables(table1, table2, ["a"], "inner")


def test_join_tables_wrong_join_type():
    table1 = pa.table({"a": [1, 2, 3], "b": [10, 20, 30]})
    table2 = pa.table({"a": [10, 20, 30], "c": [100, 200, 300]})

    with pytest.raises(ValueError):  # noqa: PT011
        join_tables(table1, table2, ["a"], "wrong")  # ty: ignore[invalid-argument-type]
