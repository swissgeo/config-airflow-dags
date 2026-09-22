# ruff: noqa: PT011
import pyarrow as pa
import pyarrow.compute as pc
import pytest
from pendulum import DateTime

from tabular.converter import convert_column


def test_convert_column_wrong_type_data():
    with pytest.raises(TypeError) as excinfo:
        convert_column("not a table", "a", lambda x: x)

    assert "pyarrow.Table" in str(excinfo.value)


def test_convert_column_wrong_type_column_type():
    data = pa.table({"a": [1, 2, 3]})

    with pytest.raises(AttributeError):
        convert_column(data, "a", str)


def test_convert_column_missing_column():
    data = pa.table({"a": [1, 2, 3]})

    with pytest.raises(ValueError):
        convert_column(data, "z", lambda x: x)


def test_convert_column_date_conversion():
    data = pa.table({"date": ["202607232100", "202202082200", "198310020830"]})

    # we need to ignore the type checker here because pyarrow is generating these
    # functions at runtime or something
    func = pc.strptime  # type: ignore

    result = convert_column(
        data,
        "date",
        func,
        converter_args={"format": "%Y%m%d%H%M", "unit": "s"},
    )

    assert result.column("date").to_pylist() == [
        DateTime(2026, 7, 23, 21, 0),
        DateTime(2022, 2, 8, 22, 0),
        DateTime(1983, 10, 2, 8, 30),
    ]
