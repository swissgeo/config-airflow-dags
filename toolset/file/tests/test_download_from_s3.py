import os
import uuid
from pathlib import Path

import boto3
import pytest

from file.download_from_s3 import download_from_s3

FIXTURES_DIR = Path(__file__).parent / "fixtures"
_fixture_files = sorted(FIXTURES_DIR.iterdir()) if FIXTURES_DIR.exists() else []

MOTO_ENDPOINT = os.environ.get("AWS_ENDPOINT_URL")
BUCKET = "bowling-alley-%s"
REGION = "eu-central-1"


@pytest.fixture
def s3_bucket():
    bucket_name = BUCKET % uuid.uuid4()
    client = boto3.client(
        "s3",
        endpoint_url=MOTO_ENDPOINT,
        region_name=REGION,
        aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
    )
    client.create_bucket(
        # for concurrent testing, we need to use unique bucket names
        Bucket=bucket_name,
        CreateBucketConfiguration={"LocationConstraint": REGION},
    )

    yield client, bucket_name

    objects = client.list_objects_v2(Bucket=bucket_name).get("Contents", [])
    for obj in objects:
        client.delete_object(Bucket=bucket_name, Key=obj["Key"])
    client.delete_bucket(Bucket=bucket_name)


def test_download_file_content(s3_bucket):
    content = b"hello from s3"

    client, bucket_name = s3_bucket
    client.put_object(Bucket=bucket_name, Key="data/test.txt", Body=content)

    with download_from_s3("data/test.txt", bucket_name) as result:
        assert Path(result).read_bytes() == content

    # file is removed after closing the context manager
    assert not Path(result).exists()


def test_download_preserves_extension(s3_bucket):
    content = b"parquet-bytes"
    client, bucket_name = s3_bucket
    client.put_object(Bucket=bucket_name, Key="archive.parquet", Body=content)

    with download_from_s3("archive.parquet", bucket_name) as result:
        assert Path(result).read_bytes() == content
        assert result.endswith(".parquet")


def test_download_missing_key_raises(s3_bucket):
    _, bucket_name = s3_bucket
    with pytest.raises(FileNotFoundError, match=r"missing.txt"):  # noqa: SIM117
        with download_from_s3("missing.txt", bucket_name):
            pass
