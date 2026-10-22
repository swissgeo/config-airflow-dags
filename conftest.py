import contextlib
import os
import uuid
from collections.abc import Generator
from typing import Literal, cast

import boto3
import psycopg
import pytest
from psycopg import sql
from pyiceberg.catalog import Catalog
from pyiceberg.catalog import load_catalog as pyiceberg_load_catalog
from types_boto3_s3 import S3Client
from types_boto3_s3.literals import BucketLocationConstraintType

Bucket = Literal["raw", "sanitize", "load"]

_BUCKET_ENV_VARS: dict[Bucket, str] = {
    "raw": "RAW_TABLE_BUCKET_ARN",
    "sanitize": "SANITIZE_TABLE_BUCKET_ARN",
    "load": "LOAD_TABLE_BUCKET_ARN",
}


@contextlib.contextmanager
def _make_catalog(bucket: Bucket) -> Generator[tuple[Catalog, str]]:
    "Create an iceberg catalog and delete if after using"
    bucket_env_var = _BUCKET_ENV_VARS[bucket]

    catalog = pyiceberg_load_catalog(
        "local",
        **{
            "type": "rest",
            "uri": os.environ["ICEBERG_URI"],
            "warehouse": os.environ[bucket_env_var],
            "s3.endpoint": os.environ["AWS_ENDPOINT_URL"],
            "s3.path-style-access": "true",
            "s3.access-key-id": os.environ["AWS_ACCESS_KEY_ID"],
            "s3.secret-access-key": os.environ["AWS_SECRET_ACCESS_KEY"],
            "s3.region": os.environ.get("AWS_REGION", "eu-central-1"),
        },
    )
    namespace = f"test_{uuid.uuid4().hex[:8]}"
    catalog.create_namespace(namespace)

    yield catalog, namespace

    if catalog and namespace:
        for table_id in catalog.list_tables(namespace):
            catalog.drop_table(table_id)
        catalog.drop_namespace(namespace)


@pytest.fixture
def raw_catalog() -> Generator[tuple[Catalog, str]]:
    with _make_catalog("raw") as (catalog, namespace):
        yield catalog, namespace


@pytest.fixture
def santitize_catalog() -> Generator[tuple[Catalog, str]]:
    with _make_catalog("sanitize") as (catalog, namespace):
        yield catalog, namespace


@pytest.fixture
def load_catalog() -> Generator[tuple[Catalog, str]]:
    with _make_catalog("load") as (catalog, namespace):
        yield catalog, namespace


@pytest.fixture
def postgres_connection() -> Generator[psycopg.Connection]:
    with psycopg.connect(
        host=os.environ["FEATURES_DB_ENDPOINT"],
        port=os.environ["FEATURES_DB_PORT"],
        dbname=os.environ["FEATURES_DB_NAME"],
        user=os.environ["FEATURES_DB_USER"],
        password=os.environ["FEATURES_DB_PASSWORD"],
    ) as conn:
        yield conn


@pytest.fixture
def postgres_table(
    postgres_connection: psycopg.Connection,
) -> Generator[tuple[psycopg.Connection, str]]:
    """Create a temporary table and yield (connection, qualified_table_name).

    The table has a fixed schema: id INTEGER, label TEXT.
    It is dropped after the test regardless of outcome.
    """

    # using unique names for concurrent testing
    table_name = f"test_{uuid.uuid4().hex[:8]}"

    with postgres_connection.cursor() as cur:
        query = sql.SQL("CREATE TABLE {} (id INTEGER, label TEXT)").format(
            sql.Identifier(table_name)
        )
        cur.execute(query)
        postgres_connection.commit()

    yield postgres_connection, table_name

    with postgres_connection.cursor() as cur:
        query = sql.SQL("DROP TABLE IF EXISTS {}").format(sql.Identifier(table_name))
        cur.execute(query)
        postgres_connection.commit()


@pytest.fixture(scope="session")
def landing_zone() -> Generator[tuple[S3Client, str]]:
    # use unique names for concurrent testing
    bucket_name = f"{os.environ['LANDING_ZONE_BUCKET']}_{uuid.uuid4().hex[:8]}"
    region = cast("BucketLocationConstraintType", os.environ.get("AWS_REGION", "eu-central-1"))

    s3 = boto3.client(
        "s3",
        endpoint_url=os.environ["AWS_ENDPOINT_URL"],
        aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
        region_name=region,
    )

    with contextlib.suppress(s3.exceptions.BucketAlreadyOwnedByYou):
        s3.create_bucket(
            Bucket=bucket_name, CreateBucketConfiguration={"LocationConstraint": region}
        )

    yield s3, bucket_name

    for page in s3.get_paginator("list_objects_v2").paginate(Bucket=bucket_name):
        for obj in page.get("Contents", []):
            s3.delete_object(Bucket=bucket_name, Key=obj["Key"])
    s3.delete_bucket(Bucket=bucket_name)
