import logging
import os
import tempfile
from pathlib import Path

import boto3

logger = logging.getLogger("pipeline_toolset")


def download_from_s3(file_key: str, bucket_name: str) -> str:
    """
    Read a file from an S3 bucket and return the path to a temporary file
    where it will be stored

    Args:
        file_key (str): The S3 object key (path) of the file to download.
        bucket_name (str): The name of the S3 bucket to download from.

    Returns:
        str: The path of the downloaded file.

    """
    logger.info("Downloading file %s from bucket %s", file_key, bucket_name)

    aws_region = os.environ.get("AWS_REGION", "eu-central-1")

    s3_client = boto3.client(
        "s3",
        region_name=aws_region,
    )

    try:
        response = s3_client.get_object(Bucket=bucket_name, Key=file_key)

        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file_key).suffix) as tmp_file:
            tmp_file.write(response["Body"].read())

            return tmp_file.name

    except s3_client.exceptions.NoSuchKey as e:
        logger.exception("File %s not found in bucket %s", file_key, bucket_name)

        raise FileNotFoundError(f"File {file_key} not found in bucket {bucket_name}") from e
