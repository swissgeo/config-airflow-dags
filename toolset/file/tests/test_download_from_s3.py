import os
from pathlib import Path

import boto3
import pytest

from file.download_from_s3 import download_from_s3

FIXTURES_DIR = Path(__file__).parent / "fixtures"
_fixture_files = sorted(FIXTURES_DIR.iterdir()) if FIXTURES_DIR.exists() else []

MOTO_ENDPOINT = "http://localhost:9090"
BUCKET = "bowling-alley"
REGION = "eu-central-1"


@pytest.fixture
def s3_bucket():
    client = boto3.client(
        "s3",
        endpoint_url=MOTO_ENDPOINT,
        region_name=REGION,
        aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
    )
    client.create_bucket(
        Bucket=BUCKET,
        CreateBucketConfiguration={"LocationConstraint": REGION},
    )

    yield client

    objects = client.list_objects_v2(Bucket=BUCKET).get("Contents", [])
    for obj in objects:
        client.delete_object(Bucket=BUCKET, Key=obj["Key"])
    client.delete_bucket(Bucket=BUCKET)


def test_download_file_content(s3_bucket):
    content = b"hello from s3"
    s3_bucket.put_object(Bucket=BUCKET, Key="data/test.txt", Body=content)

    result = download_from_s3("data/test.txt", BUCKET)

    try:
        assert Path(result).read_bytes() == content
    finally:
        Path(result).unlink(missing_ok=True)


def test_download_preserves_extension(s3_bucket):
    content = b"parquet-bytes"
    s3_bucket.put_object(Bucket=BUCKET, Key="archive.parquet", Body=content)

    result = download_from_s3("archive.parquet", BUCKET)

    try:
        assert Path(result).read_bytes() == content
        assert result.endswith(".parquet")
    finally:
        Path(result).unlink(missing_ok=True)


def test_download_missing_key_raises(s3_bucket):
    with pytest.raises(FileNotFoundError, match=r"missing.txt"):
        download_from_s3("missing.txt", BUCKET)
