import datetime as dt

import pyarrow as pa
import pytest
from pyiceberg.exceptions import NoSuchTableError
from pyiceberg.schema import Schema
from pyiceberg.types import DateType, IntegerType, NestedField, StringType

from swissgeo_toolset.tabular.reader import read_from_s3tables


@pytest.fixture
def s3_table(raw_catalog):
    """Create an intermediary table on iceberg"""
    catalog, namespace = raw_catalog
    table_name = "test_table"
    identifier = f"{namespace}.{table_name}"

    table_handle = catalog.create_table(
        identifier=identifier,
        schema=Schema(
            NestedField(1, "point_id", StringType()),
            NestedField(2, "datetime", DateType()),
            NestedField(3, "value", IntegerType()),
        ),
    )

    yield {"namespace": namespace, "table_name": table_name, "table_handle": table_handle}

    catalog.drop_table(identifier)


@pytest.fixture
def s3_table_with_data(s3_table):
    """Populate the intermediary table with some data"""
    table = s3_table["table_handle"]

    data = pa.table(
        {
            "point_id": ["123", "456"],
            "datetime": [dt.date(2026, 9, 13), dt.date(2026, 9, 15)],
            "value": [42, 1337],
        }
    )

    data = data.cast(table.schema().as_arrow())

    table.overwrite(data)

    return s3_table


def test_basic_s3_reading(s3_table_with_data):
    data = read_from_s3tables(
        "raw",
        namespace=s3_table_with_data["namespace"],
        table_name=s3_table_with_data["table_name"],
    )

    assert data is not None
    assert isinstance(data, pa.Table)
    (length, _) = data.shape
    assert length == 2

    data_py = data.to_pylist()

    assert data_py[0]["point_id"] == "123"


def test_s3_reading_inexisting_table(s3_table_with_data):
    with pytest.raises(NoSuchTableError):
        read_from_s3tables(
            "raw",
            namespace=s3_table_with_data["namespace"],
            table_name="inexisting_table",
        )


def test_s3_reading_inexisting_bucket(s3_table_with_data):
    with pytest.raises(ValueError):  # noqa: PT011
        read_from_s3tables(
            "row",  # ty: ignore[invalid-argument-type]
            namespace=s3_table_with_data["namespace"],
            table_name="inexisting_table",
        )


def test_s3_reading_unset_env(s3_table_with_data, monkeypatch):
    table_name = s3_table_with_data["table_name"]
    namespace = s3_table_with_data["namespace"]

    monkeypatch.delenv("RAW_TABLE_BUCKET_ARN")

    with pytest.raises(RuntimeError):
        read_from_s3tables(
            "raw",
            namespace=namespace,
            table_name=table_name,
        )
