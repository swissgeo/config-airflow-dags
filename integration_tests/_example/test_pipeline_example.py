from pyiceberg.schema import Schema
from pyiceberg.types import IntegerType, NestedField, StringType

from DAG._example.pipeline_example import first_step


def test_pipeline_example(raw_catalog, landing_zone):
    """Download a CSV file, parse it and put the content in a s3 table"""
    s3, bucket_name = landing_zone

    catalog, namespace = raw_catalog
    table_name = "data"
    identifier = f"{namespace}.{table_name}"

    table_handle = catalog.create_table(
        identifier=identifier,
        schema=Schema(
            NestedField(1, "id", IntegerType()),
            NestedField(2, "name", StringType()),
            NestedField(3, "value", IntegerType()),
        ),
    )

    s3.put_object(
        Bucket=bucket_name,
        Key="data.csv",
        Body="id,name,value\n1,alice,100\n2,bob,200\n3,charlie,300\n",
    )

    first_step("data.csv")

    table_handle.refresh()
    result_data = table_handle.scan().to_arrow().to_pylist()

    assert result_data == [
        {"id": 1, "name": "alice", "value": 100},
        {"id": 2, "name": "bob", "value": 200},
        {"id": 3, "name": "charlie", "value": 300},
    ]
