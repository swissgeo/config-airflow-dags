from collections.abc import Callable

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from tabular.parser.parse_parquet import parse_parquet


@pytest.fixture
def parquet(tmp_path) -> Callable[[str, pa.Table], str]:
    def create(filename, table: pa.Table) -> str:
        file_path = tmp_path / filename
        pq.write_table(table, str(file_path))
        return str(file_path)

    return create


def test_returns_table(parquet):
    table = pa.table({"name": ["Donny", "Walter"], "age": [30, 25]})
    path = parquet("basic.parquet", table)

    result = parse_parquet(path)

    assert isinstance(result, pa.Table)


def test_correct_shape(parquet):
    table = pa.table({"city": ["Bern", "Zurich"], "pop": [134000, 430000]})
    path = parquet("cities.parquet", table)

    result = parse_parquet(path)

    assert result.num_rows == 2
    assert result.column_names == ["city", "pop"]


def test_values_preserved(parquet):
    table = pa.table({"name": ["Rüdisüüli"], "city": ["Zürich"]})
    path = parquet("unicode.parquet", table)

    result = parse_parquet(path)

    assert result.column("name")[0].as_py() == "Rüdisüüli"
    assert result.column("city")[0].as_py() == "Zürich"


def test_invalid_file_raises(tmp_path):
    bad_file = tmp_path / "bad.parquet"
    bad_file.write_bytes(b"not a parquet file")

    with pytest.raises(pa.lib.ArrowInvalid):
        parse_parquet(str(bad_file))


def test_missing_file_raises():
    with pytest.raises(FileNotFoundError):
        parse_parquet("/nonexistent/path/file.parquet")
