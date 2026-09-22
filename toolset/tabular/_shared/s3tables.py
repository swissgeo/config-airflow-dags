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

    logger.info("Loading catalog for region {region} for bucket {table_bucket_arn}")

    # provide the possibility to connect either to
    # * a local iceberg API for testing, or
    # * s3tables in the cloud

    uri = os.environ.get("ICEBERG_REST_URI", f"https://s3tables.{region}.amazonaws.com/iceberg")
    warehouse = os.environ.get("ICEBERG_WAREHOUSE", table_bucket_arn)

    props: dict[str, str] = {"type": "rest", "warehouse": warehouse, "uri": uri}

    if "ICEBERG_REST_URI" in os.environ:
        # connecting locally to iceberg
        props.update(
            {
                "s3.endpoint": os.environ["AWS_ENDPOINT_URL"],
                "s3.path-style-access": "true",
                "s3.access-key-id": os.environ["AWS_ACCESS_KEY_ID"],
                "s3.secret-access-key": os.environ["AWS_SECRET_ACCESS_KEY"],
                "s3.region": os.environ.get("AWS_REGION", "eu-central-1"),
            }
        )
    else:
        # connecting in the cloud to s3tables
        props.update(
            {
                "rest.sigv4-enabled": "true",
                "rest.signing-name": "s3tables",
                "rest.signing-region": region,
            }
        )

    catalog = pyiceberg_load_catalog("s3tables", **props)

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
    except KeyError as e:
        raise ValueError(
            f"Invalid bucket: {bucket}, expected one of {_BUCKET_ENV_VARS.keys()}"
        ) from e

    try:
        return os.environ[env_var]
    except KeyError:
        raise RuntimeError(f"Environment variable {env_var} is not set") from None
