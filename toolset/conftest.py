import os
import uuid
from collections.abc import Callable, Generator
from typing import Literal

import psycopg
import pytest
from psycopg import sql
from pyiceberg.catalog import Catalog
from pyiceberg.catalog import load_catalog as pyiceberg_load_catalog

Bucket = Literal["raw", "sanitize", "load"]

_BUCKET_ENV_VARS: dict[Bucket, str] = {
    "raw": "RAW_TABLE_BUCKET_ARN",
    "sanitize": "SANITIZE_TABLE_BUCKET_ARN",
    "load": "LOAD_TABLE_BUCKET_ARN",
}


@pytest.fixture
def iceberg_catalog() -> Generator[Callable[[Bucket], tuple[Catalog, str]]]:
    """Yield function that returns (catalog, namespace) backed by the
    local Iceberg REST container. The function takes the desired bucket raw | sanitize | load

    A fresh namespace is created per test and torn down afterwards.
    """
    catalog: Catalog | None = None
    namespace: str | None = None

    def _catalog(bucket: Bucket) -> tuple[Catalog, str]:
        "Function return by the fixture to create a catalog taking a parameter"
        nonlocal catalog
        nonlocal namespace

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

        return catalog, namespace

    yield _catalog

    if catalog and namespace:
        for table_id in catalog.list_tables(namespace):
            catalog.drop_table(table_id)
        catalog.drop_namespace(namespace)


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
