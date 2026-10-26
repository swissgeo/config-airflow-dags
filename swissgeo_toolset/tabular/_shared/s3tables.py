import logging
import os
from collections.abc import Generator
from contextlib import contextmanager
from typing import Literal

from pyiceberg.catalog import Catalog
from pyiceberg.catalog import load_catalog as pyiceberg_load_catalog

logger = logging.getLogger("pipeline_toolset")

Bucket = Literal["raw", "sanitize", "load"]

_BUCKET_ENV_VARS: dict[Bucket, str] = {
    "raw": "RAW_TABLE_BUCKET_ARN",
    "sanitize": "SANITIZE_TABLE_BUCKET_ARN",
    "load": "LOAD_TABLE_BUCKET_ARN",
}


def _load_local_iceberg_catalog(table_bucket_arn: str) -> Catalog:
    """Connect to a iceberg instance and return a catalog"""

    iceberg_props = {
        "uri": os.environ["ICEBERG_URI"],
        "type": "rest",
        "warehouse": table_bucket_arn,
        "s3.endpoint": os.environ["AWS_ENDPOINT_URL"],
        "s3.path-style-access": "true",
        "s3.access-key-id": os.environ["AWS_ACCESS_KEY_ID"],
        "s3.secret-access-key": os.environ["AWS_SECRET_ACCESS_KEY"],
        "s3.region": os.environ.get("AWS_REGION", "eu-central-1"),
    }

    logger.info("Loading local iceberg catalog for bucket %s", table_bucket_arn)

    return pyiceberg_load_catalog("s3tables", **iceberg_props)


def _load_s3tables_catalog(table_bucket_arn: str) -> Catalog:  # pragma: no cover
    """Connect to AWS s3 tables and return a catalog"""

    region = os.environ.get("AWS_REGION", "eu-central-1")

    s3tables_props = {
        "uri": f"https://s3tables.{region}.amazonaws.com/iceberg",
        "type": "rest",
        "warehouse": table_bucket_arn,
        "rest.sigv4-enabled": "true",
        "rest.signing-name": "s3tables",
        "rest.signing-region": region,
    }

    logger.info("Loading s3tables catalog for region %s for bucket %s", region, table_bucket_arn)
    return pyiceberg_load_catalog("s3tables", **s3tables_props)


@contextmanager
def iceberg_catalog(table_bucket_arn: str) -> Generator[Catalog]:
    """Load an iceberg or pyiceberg catalog

    Connect to apache iceberg and return a handle.
    Depending on the env variable ICEBERG_BACKEND it either connects to
    a s3tables bucket or to a iceberg instance
    """

    catalog: Catalog | None = None

    try:
        if os.getenv("ICEBERG_BACKEND", "s3tables") == "local":
            catalog = _load_local_iceberg_catalog(table_bucket_arn)
        else:
            catalog = _load_s3tables_catalog(table_bucket_arn)  # pragma: no cover

        yield catalog

    finally:
        logger.info("Closing iceberg catalog")

        if catalog:
            catalog.close()


def get_table_bucket_arn(bucket: Bucket) -> str:
    """Return the bucket ARN from the env for the given bucket

    Args:
        bucket: The bucket to get the ARN for

    Returns:
        The bucket ARN from the environment
    """
    try:
        env_var = _BUCKET_ENV_VARS[bucket]
    except KeyError as e:
        raise ValueError(
            f"Invalid bucket: {bucket}, expected one of {_BUCKET_ENV_VARS.keys()}"
        ) from e

    try:
        return os.environ[env_var]
    except KeyError:
        raise RuntimeError(f"Environment variable {env_var} is not set") from None
