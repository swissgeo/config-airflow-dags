import os
import uuid
from collections.abc import Generator
from pathlib import Path

import pytest
from pyiceberg.catalog import Catalog
from pyiceberg.catalog import load_catalog as pyiceberg_load_catalog

# ---------------------------------------------------------------------------
# Load .env.default (project root) before collection; os.environ.setdefault
# means real env vars always win.
# ---------------------------------------------------------------------------
_ENV_FILE = Path(__file__).parent.parent / ".env.default"

if _ENV_FILE.exists():
    for _line in _ENV_FILE.read_text().splitlines():
        _line = _line.strip()
        if not _line or _line.startswith("#"):
            continue
        _key, _, _value = _line.partition("=")
        os.environ.setdefault(_key.strip(), _value.strip())


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def iceberg_catalog() -> Generator[tuple[Catalog, str]]:
    """Yield (catalog, namespace) backed by the local Iceberg REST container.

    A fresh namespace is created per test and torn down afterwards.
    Requires ICEBERG_REST_URI and ICEBERG_WAREHOUSE to be set (via .env.default).
    """
    catalog = pyiceberg_load_catalog(
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
    )
    namespace = f"test_{uuid.uuid4().hex[:8]}"
    catalog.create_namespace(namespace)

    yield catalog, namespace

    for table_id in catalog.list_tables(namespace):
        catalog.drop_table(table_id)
    catalog.drop_namespace(namespace)
