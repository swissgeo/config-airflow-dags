from collections.abc import Callable

import pyarrow as pa
import pytest

from tabular.parser.parse_csv import parse_csv


@pytest.fixture
def csv(tmp_path) -> Callable[[str, str, str], str]:
    def create(filename, content, encoding="utf-8") -> str:
        """Helper function to create CSV files to be used in the tests"""

        file_path = tmp_path / filename
        file_path.write_bytes(content.encode(encoding))

        return str(file_path)

    return create
    # since tmp_path is a pytest fixture that will get torn down, we don't
    # have to explicitly remove the temporary file


def test_basic_comma_delimited(csv):
    path = csv("basic.csv", "name,age\nDonny,30\nMaud,25")

    table = parse_csv(path, encoding="utf-8", delimiter=",")

    assert isinstance(table, pa.Table)
    assert table.num_rows == 2
    assert table.column_names == ["name", "age"]


def test_semicolon_delimiter(csv):
    path = csv("semi.csv", "city;pop\nBern;134000\nZurich;430000")

    table = parse_csv(path, encoding="utf-8", delimiter=";")

    assert table.num_rows == 2
    assert table.column_names == ["city", "pop"]


def test_custom_quote_char(csv):
    path = csv("quoted.csv", "name,note\n'Jeff','has, comma'\nWalter,plain")

    table = parse_csv(path, encoding="utf-8", delimiter=",", quote_char="'")

    assert table.column("note")[0].as_py() == "has, comma"


def test_latin1_encoding(csv):
    path = csv("latin1.csv", "name,city\nMüller,Zürich", encoding="latin-1")

    table = parse_csv(path, encoding="latin-1", delimiter=",")

    assert table.column("name")[0].as_py() == "Müller"


def test_non_csv_data(csv):
    path = csv("latin1.csv", "Non CSV DATA")

    with pytest.raises(pa.lib.ArrowInvalid):
        parse_csv(path, encoding="latin-1", delimiter=",")


def test_missing_file_raises():
    with pytest.raises(FileNotFoundError):
        parse_csv("/nonexistent/path/file.csv", encoding="utf-8", delimiter=",")
