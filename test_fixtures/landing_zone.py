import contextlib
import os
import uuid
from collections.abc import Generator
from typing import cast

import boto3
import pytest
from types_boto3_s3 import S3Client
from types_boto3_s3.literals import BucketLocationConstraintType


@pytest.fixture(scope="session")
def landing_zone() -> Generator[tuple[S3Client, str]]:
    # use unique names for concurrent testing
    bucket_name = f"{os.environ['LANDING_ZONE_BUCKET']}_{uuid.uuid4().hex[:8]}"
    region = cast("BucketLocationConstraintType", os.environ.get("AWS_REGION", "eu-central-1"))

    s3 = boto3.client(
        "s3",
        endpoint_url=os.environ["AWS_ENDPOINT_URL"],
        aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
        region_name=region,
    )

    with contextlib.suppress(s3.exceptions.BucketAlreadyOwnedByYou):
        s3.create_bucket(
            Bucket=bucket_name, CreateBucketConfiguration={"LocationConstraint": region}
        )

    yield s3, bucket_name

    for page in s3.get_paginator("list_objects_v2").paginate(Bucket=bucket_name):
        for obj in page.get("Contents", []):
            s3.delete_object(Bucket=bucket_name, Key=obj["Key"])
    s3.delete_bucket(Bucket=bucket_name)
