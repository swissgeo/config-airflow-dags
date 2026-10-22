from collections.abc import Callable

import pyarrow as pa
import pytest

from toolset.tabular.parser.parse_csv import parse_csv


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


def test_embedded_newlines(csv):
    path = csv("newlines.csv", "name,note\nDonny,'has\nembedded'\nMaud,plain")

    # with pytest.raises(pa.lib.ArrowInvalid):
    table = parse_csv(path, encoding="utf-8", delimiter=",", quote_char="'")

    assert table.column("note")[0].as_py() == "has\nembedded"


def test_empty_lines(csv):
    path = csv("empty_lines.csv", "name,note\nDonny,'bowls'\n\nMaud,nihilises")

    table = parse_csv(path, encoding="utf-8", delimiter=",", quote_char="'")

    assert table.column("note")[0].as_py() == "bowls"
    assert table.column("note")[1].as_py() == "nihilises"


def test_empty_strings(csv):
    path = csv("empty_strings.csv", "name,note,age\nDonny,'bowls',32\n\nMaud,,33")

    table = parse_csv(path, encoding="utf-8", delimiter=",", quote_char="'")

    assert table.column("note")[0].as_py() == "bowls"
    assert table.column("note")[1].as_py() == ""
    assert table.column("age")[0].as_py() == 32
    assert table.column("age")[1].as_py() == 33


def test_escape_characters(csv):
    path = csv("escape_characters.csv", "name,note\nDonny,'has\\'embedded'\nMaud,plain")

    table = parse_csv(path, encoding="utf-8", delimiter=",", quote_char="'")

    assert table.column("note")[0].as_py() == "has'embedded"
    assert table.column("note")[1].as_py() == "plain"


def test_one_line_csv(csv):
    path = csv("one_line.csv", "Donny,bowls")

    with pytest.raises(pa.lib.ArrowInvalid):
        parse_csv(path, encoding="utf-8", delimiter=",")
