# ruff: noqa: PT011,PGH003
import pyarrow as pa
import pyarrow.compute as pc
import pytest
from pendulum import DateTime

from toolset.tabular.converter import convert_column


def test_convert_column_inexisting_function():
    data = pa.table({"a": [1, 2, 3]})

    with pytest.raises(ValueError):
        convert_column(data, "a", "str")


def test_convert_column_date_conversion():
    data = pa.table({"date": ["202607232100", "202202082200", "198310020830"]})

    result = convert_column(
        data,
        "date",
        "strptime",
        converter_args={"format": "%Y%m%d%H%M", "unit": "s"},
    )

    assert result.column("date").to_pylist() == [
        DateTime(2026, 7, 23, 21, 0),
        DateTime(2022, 2, 8, 22, 0),
        DateTime(1983, 10, 2, 8, 30),
    ]


def test_convert_column_negate():
    data = pa.table({"a": [1, 2, 3]})
    result = convert_column(data, "a", "negate")
    assert result.column("a").to_pylist() == [-1, -2, -3]


def test_convert_column_negate_native_func():
    data = pa.table({"a": [1, 2, 3]})
    with pytest.raises(TypeError):
        convert_column(data, "a", pc.negate)  # type: ignore


def test_convert_column_not_pyarrow():
    data = {"a": [1, 2, 3]}

    with pytest.raises(TypeError):
        convert_column(data, "a", "negate")


def test_convert_column_inexisting_column():
    data = pa.table({"a": [1, 2, 3]})
    with pytest.raises(ValueError):
        convert_column(data, "b", "negate")
