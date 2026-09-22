import logging
import os

import pyarrow as pa
from pyiceberg.typedef import Identifier

from tabular._shared.s3tables import Bucket, get_table_bucket_arn, iceberg_catalog

logger = logging.getLogger("pipeline_toolset")

"""
Configuration class for S3 table settings.
"""


def write_to_s3tables(
    data: pa.Table,
    bucket: Bucket,
    namespace: str,
    table_name: str,
) -> Identifier:
    """
    Writes data to an S3 table using PyIceberg.

    The tables are presupposed to exist

    Args:
        data: PyArrow Table to write
        bucket: The S3 bucket to write to: raw | sanitize | load
        namespace: The namespace of the table (usually name connected to the dataset)
        table_name: The name of the table to write to
    Returns:
        The name of the S3 table
    """
    region = os.environ.get("AWS_REGION", "eu-central-1")

    with iceberg_catalog(region, get_table_bucket_arn(bucket)) as catalog:
        table_identifier = f"{namespace}.{table_name}"
        table_handle = catalog.load_table(table_identifier)

        table_schema = table_handle.schema().as_arrow()

        logger.info(f"Casting data schema to {table_schema}")
        # we need to cast the data into the given schema. The reason for that is that pyarrow's
        # internal schema might have nullable columns (if it's inferred from the data source)
        # whereas the table schema might require these columns to be non-nullable. Casting ensures
        # the data matches the table schema.
        data = data.cast(table_schema)

        logger.info(f"Writing table {table_handle.name()} to S3 tables catalog")

        table_handle.overwrite(df=data)

    return data
