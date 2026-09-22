import logging
import os

import pyarrow as pa

from tabular._shared.s3tables import Bucket, get_table_bucket_arn, iceberg_catalog

logger = logging.getLogger("pipeline_toolset")


def read_from_s3tables(bucket: Bucket, namespace: str, table_name: str) -> pa.Table:
    """Read a table from an S3 tables catalog.

    Args:
        bucket: which bucket to read from: raw | sanitize | load
        namespace: The namespace of the table.
        table_name: The name of the table.

    Returns:
        The table as a PyArrow table.
    """
    table_identifier = f"{namespace}.{table_name}"

    region = os.environ.get("AWS_REGION", "eu-central-1")

    table_bucket_arn = get_table_bucket_arn(bucket)

    logger.info(f"Reading table {table_identifier} from s3 table bucket {table_bucket_arn}")

    with iceberg_catalog(region, table_bucket_arn) as catalog:
        if not catalog.table_exists(table_identifier):
            raise FileNotFoundError(f"S3 table {table_identifier} not found")

        table = catalog.load_table(table_identifier)

        return table.scan().to_arrow()
