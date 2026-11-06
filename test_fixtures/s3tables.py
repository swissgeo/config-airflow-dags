import contextlib
import json
import os
import uuid
from collections.abc import Generator
from pathlib import Path
from typing import Literal

import pytest
from pyiceberg.catalog import Catalog
from pyiceberg.catalog import load_catalog as pyiceberg_load_catalog
from pyiceberg.schema import Schema

Bucket = Literal["raw", "sanitize", "load"]

_BUCKET_ENV_VARS: dict[Bucket, str] = {
    "raw": "RAW_TABLE_BUCKET_ARN",
    "sanitize": "SANITIZE_TABLE_BUCKET_ARN",
    "load": "LOAD_TABLE_BUCKET_ARN",
}


### CLASS SCOPING
# These fixtures are class scoped. This allows for keeping the same catalog for all tests in
# a class. If tests aren't in a class, then the fixtures are function scoped and a new catalog
# is created for each test.


@pytest.fixture(scope="class")
def s3tables_namespace():
    return f"test_{uuid.uuid4().hex[:8]}"


@contextlib.contextmanager
def _make_catalog(bucket: Bucket, s3tables_namespace: str) -> Generator[Catalog]:
    "Create an iceberg catalog and delete if after using"
    bucket_env_var = _BUCKET_ENV_VARS[bucket]

    catalog = pyiceberg_load_catalog(
        bucket,
        **{
            "type": "rest",
            "uri": os.environ[bucket_env_var],
            "s3.endpoint": os.environ["AWS_ENDPOINT_URL"],
            "s3.path-style-access": "true",
            "s3.access-key-id": os.environ["AWS_ACCESS_KEY_ID"],
            "s3.secret-access-key": os.environ["AWS_SECRET_ACCESS_KEY"],
            "s3.region": os.environ.get("AWS_REGION", "eu-central-1"),
        },
    )
    catalog.create_namespace(
        s3tables_namespace,
        properties={"location": f"s3://{os.environ[bucket_env_var]}/{s3tables_namespace}"},
    )

    yield catalog

    if catalog and s3tables_namespace:
        for table_id in catalog.list_tables(s3tables_namespace):
            catalog.drop_table(table_id)
        catalog.drop_namespace(s3tables_namespace)


@pytest.fixture(scope="class")
def raw_catalog(s3tables_namespace) -> Generator[Catalog]:
    with _make_catalog("raw", s3tables_namespace) as (catalog):
        yield catalog


@pytest.fixture(scope="class")
def sanitize_catalog(s3tables_namespace) -> Generator[Catalog]:
    with _make_catalog("sanitize", s3tables_namespace) as (catalog):
        yield catalog


@pytest.fixture(scope="class")
def load_catalog(s3tables_namespace) -> Generator[Catalog]:
    with _make_catalog("load", s3tables_namespace) as (catalog):
        yield catalog


def _create_s3tables_with_model(schema_file, catalog, s3tables_namespace) -> tuple[str, str]:
    """
    Create a table in a given catalog and namespace based on the
    schema definition in models
    """
    path = Path("models/s3tables/models/") / schema_file
    with open(path) as f:
        schema = json.load(f)

    table_name = schema["name"]
    table_schema = schema["metadata"]["iceberg"]["schema"]

    iceberg_schema = Schema.model_validate(table_schema)
    table_identifier = f"{s3tables_namespace}.{table_name}"
    catalog.create_table(table_identifier, iceberg_schema)

    return table_name, table_identifier


@pytest.fixture(scope="class")
def s3tables_table_raw(s3tables_namespace, raw_catalog: Catalog):
    table_identifier: str

    def _make(schema_file: str) -> str:
        nonlocal table_identifier

        table_name, table_identifier = _create_s3tables_with_model(
            schema_file, raw_catalog, s3tables_namespace
        )
        return table_name

    yield _make

    raw_catalog.drop_table(table_identifier)


@pytest.fixture(scope="class")
def s3tables_table_sanitize(s3tables_namespace, sanitize_catalog: Catalog):
    table_identifier: str

    def _make(schema_file: str) -> str:
        nonlocal table_identifier

        table_name, table_identifier = _create_s3tables_with_model(
            schema_file, sanitize_catalog, s3tables_namespace
        )
        return table_name

    yield _make

    sanitize_catalog.drop_table(table_identifier)


@pytest.fixture(scope="class")
def s3tables_table_load(s3tables_namespace, load_catalog: Catalog):
    table_identifier: str

    def _make(schema_file: str) -> str:
        nonlocal table_identifier

        table_name, table_identifier = _create_s3tables_with_model(
            schema_file, load_catalog, s3tables_namespace
        )

        return table_name

    yield _make

    load_catalog.drop_table(table_identifier)
