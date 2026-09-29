import os
from pathlib import Path

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
