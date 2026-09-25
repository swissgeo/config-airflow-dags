import pyarrow as pa

from tabular.converter.lowercase_column_names import lowercase_column_names


def test_already_lowercase():
    data = pa.table({"a": [1, 2], "b": [3, 4]})
    result = lowercase_column_names(data)
    assert result.column_names == ["a", "b"]


def test_uppercase_columns():
    data = pa.table({"A": [1, 2], "B": [3, 4]})
    result = lowercase_column_names(data)
    assert result.column_names == ["a", "b"]


def test_mixed_case_columns():
    data = pa.table({"FooBar": [1], "BAZ": [2], "qux": [3]})
    result = lowercase_column_names(data)
    assert result.column_names == ["foobar", "baz", "qux"]


def test_values_preserved():
    data = pa.table({"NAME": ["alice", "bob"], "AGE": [30, 40]})
    result = lowercase_column_names(data)
    assert result.column("name").to_pylist() == ["alice", "bob"]
    assert result.column("age").to_pylist() == [30, 40]


def test_empty_table():
    data = pa.table({"ID": pa.array([], type=pa.int32())})
    result = lowercase_column_names(data)
    assert result.column_names == ["id"]
    assert result.num_rows == 0
