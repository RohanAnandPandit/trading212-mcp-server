import hashlib
import json
import os
from pathlib import Path

import hishel


def create_storage(base_url: str, authorization: str) -> hishel.FileStorage:
    """Isolate persistent responses by API base URL and full credentials."""
    identity = json.dumps(
        [base_url, authorization], separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")
    fingerprint = hashlib.sha256(identity).hexdigest()
    # A new root prevents reuse of entries from the legacy shared cache.
    base_path = (Path(".cache/trading212-v2") / fingerprint).resolve()
    base_path.mkdir(mode=0o700, parents=True, exist_ok=True)
    if os.name == "posix":
        base_path.chmod(0o700)
    return hishel.FileStorage(base_path=base_path, ttl=300)


# The API exposes non-idempotent POST endpoints for orders, pies, and exports,
# so we only cache GET requests.
controller = hishel.Controller(
    # Cache only GET methods
    cacheable_methods=["GET"],

    # Cache only 200 status codes
    cacheable_status_codes=[200],

    # Use a stale response if a connection issue prevents obtaining a new one.
    allow_stale=True,

    force_cache=True,
)
