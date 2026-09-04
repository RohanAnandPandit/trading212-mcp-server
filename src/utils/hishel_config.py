"""Credential-isolated caching with shared storage locks within a process.

Hishel 0.1.2 does not include Authorization in its default cache key. Without
an upstream Vary header, one shared directory can return another account's
response. Separate directories isolate identities; reusing storage within
each directory lets same-identity clients share Hishel's file lock.
"""

import hashlib
import json
import os
from pathlib import Path
from threading import Lock
from weakref import WeakValueDictionary

import hishel


# Clients keep their storage alive. The registry must not retain every account
# ever used; removing a weak entry does not delete its persistent cache files.
_storages: WeakValueDictionary[Path, hishel.FileStorage] = WeakValueDictionary()
# Protect lookup AND creation so simultaneous callers cannot get separate locks
# for the same directory. This registry lock is not held during HTTP requests.
_storages_lock = Lock()


def create_storage(base_url: str, authorization: str) -> hishel.FileStorage:
    """Return this process's shared storage for the resolved account namespace.

    Pass the actual outgoing Authorization value, including Basic credentials,
    so a secret change also changes the namespace. This does not coordinate
    concurrent file access between separate server processes.
    """
    # JSON preserves field boundaries; hashing keeps raw credentials out of
    # directory names. The digest is an identifier, not encryption of the cache.
    identity = json.dumps(
        [base_url, authorization], separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")
    fingerprint = hashlib.sha256(identity).hexdigest()
    # A new root prevents reuse of entries from the legacy shared cache. Resolve
    # the path so different working directories cannot share a registry entry.
    base_path = (Path(".cache/trading212-v2") / fingerprint).resolve()
    # Hishel's file locks belong to each storage instance. Reuse that instance
    # within this process so clients cannot read each other's partial writes.
    with _storages_lock:
        storage = _storages.get(base_path)
        if storage is None:
            base_path.mkdir(mode=0o700, parents=True, exist_ok=True)
            if os.name == "posix":
                base_path.chmod(0o700)
            storage = hishel.FileStorage(base_path=base_path, ttl=300)
            _storages[base_path] = storage
        return storage


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
