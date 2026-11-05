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
def sanitize_catalog() -> Generator[tuple[Catalog, str]]:
    with _make_catalog("sanitize") as (catalog, namespace):
        yield catalog, namespace


@pytest.fixture
def load_catalog() -> Generator[tuple[Catalog, str]]:
    with _make_catalog("load") as (catalog, namespace):
        yield catalog, namespace


@pytest.fixture
def s3tables_table(raw_catalog, sanitize_catalog, load_catalog):
    """Create a table in s3tables based on the definition of a model file
    that resides in models/s3tables
    """
    catalog: Catalog
    table_identifier: str

    def _make(schema_file: str, bucket: str) -> tuple[str, str]:
        nonlocal table_identifier, catalog

        path = Path("models/s3tables/models/") / schema_file
        with open(path) as f:
            schema = json.load(f)

        table_name = schema["name"]
        table_schema = schema["metadata"]["iceberg"]["schema"]

        if bucket == "raw":
            catalog_data = raw_catalog
        elif bucket == "sanitize":
            catalog_data = sanitize_catalog
        elif bucket == "load":
            catalog_data = load_catalog

        catalog, namespace = catalog_data

        iceberg_schema = Schema.model_validate(table_schema)
        table_identifier = f"{namespace}.{table_name}"
        catalog.create_table(table_identifier, iceberg_schema)

        return table_name, namespace

    yield _make

    catalog.drop_table(table_identifier)
    # namespace is being dropped by the catalog fixture
