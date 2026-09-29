import logging

import pyarrow as pa

from toolset.tabular._shared.s3tables import Bucket, get_table_bucket_arn, iceberg_catalog

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

    table_bucket_arn = get_table_bucket_arn(bucket)

    logger.info("Reading table %s from s3 table bucket %s", table_identifier, table_bucket_arn)

    with iceberg_catalog(table_bucket_arn) as catalog:
        table = catalog.load_table(table_identifier)

        return table.scan().to_arrow()
