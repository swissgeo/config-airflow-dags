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
    with pytest.raises(ValueError):
        rename_column(data, "z", "new")


def test_rename_column_wrong_type_table():
    # passing a non-pyarrow object will fail when accessing .column_names
    with pytest.raises(AttributeError) as excinfo:
        rename_column("not a table", "a", "b")

    assert "column_names" in str(excinfo.value)


def test_rename_column_allows_duplicate_target_name():
    # renaming 'a' to 'b' will produce duplicate column names if 'b' already exists
    data = pa.table({"a": [1, 2], "b": [3, 4]})

    result = rename_column(data, "a", "b")

    # both columns named 'b'
    assert result.column_names.count("b") == 2

    # verify column order and values by index (to distinguish duplicates)
    assert result.column(0).to_pylist() == [1, 2]  # original 'a'
    assert result.column(1).to_pylist() == [3, 4]  # original 'b'
