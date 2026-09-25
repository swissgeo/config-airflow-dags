# ruff: noqa: PT011
import pyarrow as pa
import pytest

from tabular.converter.rename_column import rename_column


def test_rename_column_basic():
    data = pa.table({"a": [1, 2, 3], "b": [10, 20, 30]})

    result = rename_column(data, "a", "alpha")

    # names updated and order preserved
    assert result.column_names == ["alpha", "b"]

    # values moved to the new name
    assert result.column("alpha").to_pylist() == [1, 2, 3]

    # other columns unchanged
    assert result.column("b").to_pylist() == [10, 20, 30]


def test_rename_column_missing_old_name_raises():
    data = pa.table({"a": [1, 2], "b": [3, 4]})

    # if the old name doesn't exist, we expect an error to be raised
    with pytest.raises(KeyError):
        rename_column(data, "z", "new")


def test_rename_column_wrong_type_table():
    # passing a non-pyarrow object will fail when accessing .column_names
    with pytest.raises(AttributeError) as excinfo:
        rename_column("not a table", "a", "b")

    assert "column_names" in str(excinfo.value)


def test_rename_column_no_duplicates():
    data = pa.table({"a": [1, 2], "b": [3, 4]})

    with pytest.raises(KeyError):
        # we can't rename a to b because b already exists
        rename_column(data, "a", "b")
