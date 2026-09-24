import datetime

import pyarrow as pa
import pytest
from pyiceberg.exceptions import NoSuchTableError
from pyiceberg.schema import Schema
from pyiceberg.types import DateType, IntegerType, NestedField, StringType

from tabular.writer import write_to_s3tables


@pytest.fixture
def s3_table(iceberg_catalog):
    """Create an intermediary table on iceberg"""
    catalog, namespace = iceberg_catalog
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


def test_basic_writing_to_s3tables(s3_table):
    """Test writing to an s3tables"""
    data = pa.table(
        {
            "point_id": ["123", "456"],
            "datetime": [datetime.date(2023, 1, 1), datetime.date(2023, 1, 2)],
            "value": [42, 84],
        }
    )

    return_data = write_to_s3tables(
        data=data,
        bucket="raw",
        namespace=s3_table["namespace"],
        table_name=s3_table["table_name"],
    )

    assert data.to_pydict() == return_data.to_pydict()
    table_handle = s3_table["table_handle"]
    table_handle.refresh()
    # check table if it contains the data
    table_data = table_handle.scan().to_arrow()
    assert table_data.to_pydict() == data.to_pydict()


def test_writing_to_inexisting_s3tables(s3_table):
    """Test that trying to write to an inexisting table it raises an exception"""
    data = pa.table(
        {
            "point_id": ["123", "456"],
            "datetime": [datetime.date(2023, 1, 1), datetime.date(2023, 1, 2)],
            "value": [42, 84],
        }
    )

    with pytest.raises(NoSuchTableError):
        write_to_s3tables(
            data=data,
            bucket="raw",
            namespace=s3_table["namespace"],
            table_name="inexisting",
        )


def test_basic_writing_to_s3tables_replaces_existing(s3_table):
    """Test that writing to the table replaces everything without leftovers"""

    table_handle = s3_table["table_handle"]
    initial_data = pa.table(
        {
            "point_id": ["123", "456"],
            "datetime": [datetime.date(2026, 9, 13), datetime.date(2026, 9, 15)],
            "value": [42, 1337],
        }
    )

    initial_data = initial_data.cast(table_handle.schema().as_arrow())

    table_handle.append(initial_data)

    new_data = pa.table(
        {
            "point_id": ["abc"],
            "datetime": [datetime.date(2022, 1, 1)],
            "value": [1337],
        }
    )

    write_to_s3tables(
        data=new_data,
        bucket="raw",
        namespace=s3_table["namespace"],
        table_name=s3_table["table_name"],
    )

    table_handle.refresh()
    table_data = table_handle.scan().to_arrow()
    assert table_data.to_pydict() == new_data.to_pydict()


@pytest.mark.parametrize(
    "data",
    [
        pa.table(
            {
                "point_id": ["abc"],
                "datetime": [datetime.date(2022, 1, 1)],
                "value": [1337],
                "another_column": ["this is too much"],
            }
        ),
        pa.table(
            {
                "point_id": ["abc"],
                "datetime": ["invalid date string"],
                "value": [1337],
            }
        ),
        pa.table(
            {
                "point_id": ["abc"],
                "datetime": [datetime.date(2022, 1, 1)],
                # not enough columns
            }
        ),
    ],
)
def test_write_invalid_schema(s3_table, data):
    """Test various scenarios where the schema is invalid"""
    with pytest.raises(ValueError):  # noqa: PT011
        write_to_s3tables(
            data=data,
            bucket="raw",
            namespace=s3_table["namespace"],
            table_name=s3_table["table_name"],
        )
