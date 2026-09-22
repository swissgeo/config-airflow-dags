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


@contextmanager
def iceberg_catalog(region: str, table_bucket_arn: str) -> Generator[Catalog]:
    """Load an iceberg catalog

    Connect to apache iceberg (s3 tables) and return a handle.
    """

    logger.info(f"Loading catalog for region {region} for bucket {table_bucket_arn}")

    catalog = pyiceberg_load_catalog(
        "s3tables",
        **{
            "type": "rest",
            "warehouse": table_bucket_arn,
            "uri": f"https://s3tables.{region}.amazonaws.com/iceberg",
            "rest.sigv4-enabled": "true",
            "rest.signing-name": "s3tables",
            "rest.signing-region": region,
        },
    )

    try:
        yield catalog

    finally:
        logger.info("Closing iceberg catalog")
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
    except KeyError:
        raise ValueError(f"Invalid bucket: {bucket}, expected one of {get_args(Bucket)}") from None

    try:
        return os.environ[env_var]
    except KeyError:
        raise RuntimeError(f"Environment variable {env_var} is not set") from None
