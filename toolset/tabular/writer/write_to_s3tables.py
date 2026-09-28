import logging
import os

import pyarrow as pa

from tabular._shared.s3tables import Bucket, get_table_bucket_arn, iceberg_catalog

logger = logging.getLogger("pipeline_toolset")


class WriteToS3TablesError(Exception):
    """Custom exception for write_to_s3tables errors."""


def write_to_s3tables(
    arrow_table: pa.Table,
    bucket: Bucket,
    namespace: str,
    table_name: str,
) -> pa.Table:
    """
    Writes data to an S3 table using PyIceberg.

    The tables are presupposed to exist

    Args:
        arrow_table: PyArrow Table to write
        bucket: The S3 bucket to write to: raw | sanitize | load
        namespace: The namespace of the table (usually name connected to the dataset)
        table_name: The name of the table to write to
    Returns:
        The data itself again in pyarrow format
    """
    region = os.environ.get("AWS_REGION", "eu-central-1")

    with iceberg_catalog(region, get_table_bucket_arn(bucket)) as catalog:
        table_identifier = f"{namespace}.{table_name}"
        table_handle = catalog.load_table(table_identifier)

        table_schema = table_handle.schema().as_arrow()

        if set(table_schema.names) != set(arrow_table.schema.names):
            missing_cols = list(set(table_schema.names) - set(arrow_table.schema.names))
            excess_cols = list(set(arrow_table.schema.names) - set(table_schema.names))
            raise WriteToS3TablesError(
                f"Mismatch in columns. Missing columns: {missing_cols}. "
                f"Excess columns: {excess_cols}",
            )

        # We need to cast the data into the given schema. The reason for that is that pyarrow's
        # internal schema might have nullable columns (if it's inferred from the data source)
        # whereas the table schema might require these columns to be non-nullable. Casting ensures
        # the data matches the table schema.
        # We also need to ensure that the column name order is matching
        try:
            logger.debug("Casting data schema to %s", table_schema)
            arrow_table = arrow_table.select(table_schema.names).cast(table_schema)
        except Exception as e:
            raise WriteToS3TablesError("Failed to cast data schema") from e

        logger.info("Writing table %s to S3 tables catalog", table_handle.name())

        table_handle.overwrite(df=arrow_table)

    return arrow_table
