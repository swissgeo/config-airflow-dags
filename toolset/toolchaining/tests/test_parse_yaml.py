from collections.abc import Callable

import pytest
import yaml

from toolchaining.parse_yaml import parse_yaml


@pytest.fixture
def yaml_file(tmp_path) -> Callable[[str, str], str]:
    def create(filename, content) -> str:
        file_path = tmp_path / filename
        file_path.write_text(content, encoding="utf-8")
        return str(file_path)

    return create


def test_mapping_returns_dict(yaml_file):
    path = yaml_file("config.yaml", "name: Alice\nage: 30\n")

    result = parse_yaml(path)

    assert result == {"name": "Alice", "age": 30}


def test_sequence_of_mappings_returns_list(yaml_file):
    path = yaml_file("items.yaml", "- city: Bern\n  pop: 134000\n- city: Zurich\n  pop: 430000\n")

    result = parse_yaml(path)

    assert isinstance(result, list)
    assert len(result) == 2
    assert result[0] == {"city": "Bern", "pop": 134000}


def test_unicode_values(yaml_file):
    path = yaml_file("unicode.yaml", "name: Müller\ncity: Zürich\n")

    result = parse_yaml(path)

    assert result["name"] == "Müller"
    assert result["city"] == "Zürich"


def test_invalid_yaml_raises(yaml_file):
    path = yaml_file("bad.yaml", "key: [unclosed bracket\n")

    with pytest.raises(yaml.YAMLError):
        parse_yaml(path)


def test_missing_file_raises():
    with pytest.raises(FileNotFoundError):
        parse_yaml("/nonexistent/path/file.yaml")
