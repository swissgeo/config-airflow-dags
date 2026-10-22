import os
import uuid
from pathlib import Path
from typing import cast

import boto3
import pytest
from types_boto3_s3.literals import BucketLocationConstraintType

from toolset.file.download_from_s3 import _download_from_s3, download_from_landingzone

FIXTURES_DIR = Path(__file__).parent / "fixtures"
_fixture_files = sorted(FIXTURES_DIR.iterdir()) if FIXTURES_DIR.exists() else []

MOTO_ENDPOINT = os.environ["AWS_ENDPOINT_URL"]
REGION = cast("BucketLocationConstraintType", os.environ["AWS_REGION"])


@pytest.fixture
def landing_zone():
    bucket_name = os.environ["LANDING_ZONE_BUCKET"] + f"-{uuid.uuid4()}"

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


def test_download_from_landinzone(mocker):
    mock_download = mocker.patch("toolset.file.download_from_s3._download_from_s3")

    download_from_landingzone("file.key")

    mock_download.assert_called_once_with("file.key", os.environ["LANDING_ZONE_BUCKET"])


def test_download_file_content(landing_zone):
    content = b"hello from s3"

    client, bucket_name = landing_zone
    client.put_object(Bucket=bucket_name, Key="data/test.txt", Body=content)

    with _download_from_s3("data/test.txt", bucket_name) as result:
        assert Path(result).read_bytes() == content

    # file is removed after closing the context manager
    assert not Path(result).exists()


def test_download_preserves_extension(landing_zone):
    content = b"parquet-bytes"
    client, bucket_name = landing_zone
    client.put_object(Bucket=bucket_name, Key="archive.parquet", Body=content)

    with _download_from_s3("archive.parquet", bucket_name) as result:
        assert Path(result).read_bytes() == content
        assert result.endswith(".parquet")


def test_download_missing_key_raises(landing_zone):
    _, bucket_name = landing_zone
    with pytest.raises(FileNotFoundError, match=r"missing.txt"):  # noqa: SIM117
        with _download_from_s3("missing.txt", bucket_name):
            pass
