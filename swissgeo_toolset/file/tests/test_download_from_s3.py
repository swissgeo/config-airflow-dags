import os
from pathlib import Path
from typing import cast

import pytest
from types_boto3_s3.literals import BucketLocationConstraintType

from swissgeo_toolset.file.download_from_s3 import _download_from_s3, download_from_landingzone

FIXTURES_DIR = Path(__file__).parent / "fixtures"
_fixture_files = sorted(FIXTURES_DIR.iterdir()) if FIXTURES_DIR.exists() else []

MOTO_ENDPOINT = os.environ["AWS_ENDPOINT_URL"]
REGION = cast("BucketLocationConstraintType", os.environ["AWS_REGION"])


def test_download_from_landinzone(mocker):
    mock_download = mocker.patch("swissgeo_toolset.file.download_from_s3._download_from_s3")

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
