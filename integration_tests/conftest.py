import contextlib
import os
from collections.abc import Generator
from typing import cast

import boto3
import pytest
from pyiceberg.catalog import Catalog
from pyiceberg.catalog import load_catalog as pyiceberg_load_catalog
from types_boto3_s3 import S3Client
from types_boto3_s3.literals import BucketLocationConstraintType


@pytest.fixture
def raw_catalog() -> Generator[tuple[Catalog, str]]:
    # Require local configuration rather than falling back to AWS S3 Tables.
    with pyiceberg_load_catalog(
        "local",
        **{
            "type": "rest",
            "uri": os.environ["ICEBERG_REST_URI"],
            "warehouse": os.environ["ICEBERG_WAREHOUSE"],
            "s3.endpoint": os.environ["AWS_ENDPOINT_URL"],
            "s3.path-style-access": "true",
            "s3.access-key-id": os.environ["AWS_ACCESS_KEY_ID"],
            "s3.secret-access-key": os.environ["AWS_SECRET_ACCESS_KEY"],
            "s3.region": os.environ.get("AWS_REGION", "eu-central-1"),
        },
    ) as catalog:
        # namespace = f"test_{uuid.uuid4().hex[:8]}"
        namespace = "example"  # TODO make this work maybe?
        catalog.create_namespace(namespace)

        yield catalog, namespace

        for table_id in catalog.list_tables(namespace):
            catalog.drop_table(table_id)
        catalog.drop_namespace(namespace)


@pytest.fixture
def landing_zone() -> Generator[tuple[S3Client, str]]:
    bucket_name = "landing-zone"
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
