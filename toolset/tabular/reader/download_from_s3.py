import logging
import typing

import boto3

logger = logging.getLogger("pipeline_toolset")


def download_from_s3(file_key: str, bucket_name: str) -> typing.IO[bytes]:
    """
    Read a file from an S3 bucket and return a file object.

    Args:
        file_key (str): The S3 object key (path) of the file to download.
        bucket_name (str): The name of the S3 bucket to download from.

    Returns:
        typing.IO[str]: A file object representing the downloaded file from S3.
    """
    logger.info(f"Downloading file {file_key} from bucket {bucket_name}")

    s3_client = boto3.client(
        # TODO Make this configurable
        "s3",
        region_name="eu-central-1",
    )

    try:
        response = s3_client.get_object(Bucket=bucket_name, Key=file_key)
        return response["Body"]
    except s3_client.exceptions.NoSuchKey as e:
        logger.exception(f"File {file_key} not found in bucket {bucket_name}")
        # TODO is this exception type correct?
        raise FileNotFoundError(f"File {file_key} not found in bucket {bucket_name}") from e
