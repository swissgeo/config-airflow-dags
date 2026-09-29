import contextlib
import os
import uuid
from collections.abc import Generator

import boto3
import pytest
from DAG.pipeline_example import first_step
from pyiceberg.catalog import Catalog
from pyiceberg.catalog import load_catalog as pyiceberg_load_catalog
from pyiceberg.schema import Schema
from pyiceberg.types import IntegerType, NestedField, StringType


@pytest.fixture
def raw_catalog() -> Generator[tuple[Catalog, str]]:
    # Require local configuration rather than falling back to AWS S3 Tables.
    with pyiceberg_load_catalog(
        "local",
        **{
            "type": "rest",
            "uri": os.environ["ICEBERG_REST_URI"],
            "warehouse": os.environ["ICEBERG_WAREHOUSE"],
            "s3.endpoint": os.environ["AWS_ENDPOINT_URL"],
            "s3.path-style-access": "true",
            "s3.access-key-id": os.environ["AWS_ACCESS_KEY_ID"],
            "s3.secret-access-key": os.environ["AWS_SECRET_ACCESS_KEY"],
            "s3.region": os.environ.get("AWS_REGION", "eu-central-1"),
        },
    ) as catalog:
        # namespace = f"test_{uuid.uuid4().hex[:8]}"
        namespace = "example"  # TODO make this work maybe?
        catalog.create_namespace(namespace)

        yield catalog, namespace

        for table_id in catalog.list_tables(namespace):
            catalog.drop_table(table_id)
        catalog.drop_namespace(namespace)


@pytest.fixture
def landing_zone():
    warehouse = "s3://landing_zone/"
    region = os.environ.get("AWS_REGION", "eu-central-1")

    s3 = boto3.client(
        "s3",
        endpoint_url=os.environ["AWS_ENDPOINT_URL"],
        aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
        region_name=region,
    )

    bucket_name = warehouse.replace("s3://", "").rstrip("/")

    with contextlib.suppress(s3.exceptions.BucketAlreadyOwnedByYou):
        s3.create_bucket(
            Bucket=bucket_name, CreateBucketConfiguration={"LocationConstraint": region}
        )

    return s3, bucket_name


def test_pipeline_example(raw_catalog, landing_zone):
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
