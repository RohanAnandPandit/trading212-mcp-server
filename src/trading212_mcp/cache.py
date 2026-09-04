"""Credential-free Hishel storage with serialized cross-process invalidation.

The network sender is the only component that knows credentials. Cache requests
contain an allowlist of headers; private namespaces never rely on upstream Vary.
A file lock covers request, body consumption, and invalidation across processes.
"""

import hashlib
import json
import os
import sqlite3
from collections.abc import Callable
from contextlib import closing
from contextvars import ContextVar
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

from filelock import FileLock, Timeout
from hishel import (
    BaseFilter,
    Entry,
    FilterPolicy,
    Headers,
    Request,
    Response,
    SyncCacheProxy,
    SyncSqliteStorage,
)

from .errors import RequestError
from .settings import Settings

observations: ContextVar[list[dict[str, object]] | None] = ContextVar(
    "cache_observations", default=None
)
META_KEY = "io.github.RohanAnandPandit.trading212/cache"


def private_file(path: Path) -> None:
    fd = os.open(path, os.O_CREAT | os.O_RDWR, 0o600)
    os.close(fd)
    if os.name == "posix":
        path.chmod(0o600)


class SuccessfulResponse(BaseFilter[Response]):
    def needs_body(self) -> bool:
        return False

    def apply(self, item: Response, body: bytes | None) -> bool:
        return item.status_code == 200


class NamespacedStorage(SyncSqliteStorage):
    """Generation keys make pre-mutation private entries unreachable."""

    generation: str = "0"

    def get_entries(self, key: str) -> list[Entry]:
        return super().get_entries(f"{self.generation}:{key}")

    def create_entry(
        self,
        request: Request,
        response: Response,
        key: str,
        id_: UUID | None = None,
    ) -> Entry:
        return super().create_entry(request, response, f"{self.generation}:{key}", id_)


class ResponseCache:
    def __init__(self, settings: Settings, base_url: str, authorization: str) -> None:
        digest = hashlib.sha256(
            json.dumps([base_url, authorization], separators=(",", ":")).encode()
        ).hexdigest()
        self.path = (settings.cache_dir / digest).resolve()
        self.path.mkdir(parents=True, exist_ok=True, mode=0o700)
        if os.name == "posix":
            self.path.chmod(0o700)
        for name in ("responses.sqlite", "state.sqlite", "requests.lock"):
            private_file(self.path / name)
        self.lock = FileLock(self.path / "requests.lock", timeout=30)
        self.storage = NamespacedStorage(database_path=self.path / "responses.sqlite")
        self.account_ttl = settings.account_ttl
        self.history_ttl = settings.history_ttl
        self.metadata_ttl = settings.metadata_ttl
        self.closed = False
        with (
            self.lock,
            closing(sqlite3.connect(self.path / "state.sqlite")) as state,
            state,
        ):
            state.execute(
                "CREATE TABLE IF NOT EXISTS generation (id INTEGER PRIMARY KEY CHECK (id=1), value INTEGER NOT NULL)"
            )
            state.execute("INSERT OR IGNORE INTO generation VALUES (1, 0)")

    def request(
        self, method: str, url: str, sender: Callable[[Request], Response]
    ) -> bytes:
        if self.closed:
            raise RequestError("The API client is closed.")
        path = url.split("?", 1)[0]
        metadata = "/equity/metadata/" in path
        ttl = (
            self.metadata_ttl
            if metadata
            else (
                self.history_ttl
                if "/equity/history/" in path and not path.endswith("/exports")
                else self.account_ttl
            )
        )
        request = Request(
            method=method, url=url, headers=Headers({}), metadata={"hishel_ttl": ttl}
        )
        try:
            with self.lock:
                if self.closed:
                    raise RequestError("The API client is closed.")
                with (
                    closing(sqlite3.connect(self.path / "state.sqlite")) as state,
                    state,
                ):
                    row = state.execute(
                        "SELECT value FROM generation WHERE id=1"
                    ).fetchone()
                    self.storage.generation = "metadata" if metadata else str(row[0])
                try:
                    if method == "GET" and ttl > 0:
                        proxy = SyncCacheProxy(
                            sender,
                            storage=self.storage,
                            policy=FilterPolicy(
                                response_filters=[SuccessfulResponse()]
                            ),
                        )
                        response = proxy.handle_request(request)
                    else:
                        response = sender(request)
                    # Hishel writes streaming bodies lazily: consume while holding the lock.
                    body = response.read()
                    recorded = observations.get()
                    if recorded is not None:
                        fetched = response.headers.get("x-trading212-retrieved-at")
                        recorded.append(
                            {
                                "cacheHit": bool(
                                    response.metadata.get("hishel_from_cache", False)
                                ),
                                "retrievedAt": datetime.fromtimestamp(
                                    float(fetched), UTC
                                ).isoformat()
                                if fetched is not None
                                else datetime.now(UTC).isoformat(),
                                "ttlSeconds": ttl if method == "GET" else 0,
                            }
                        )
                    return body
                finally:
                    if method != "GET":
                        # Conservative even on errors: the server may have applied a mutation.
                        with (
                            closing(
                                sqlite3.connect(self.path / "state.sqlite")
                            ) as state,
                            state,
                        ):
                            state.execute(
                                "UPDATE generation SET value=value+1 WHERE id=1"
                            )
        except Timeout:
            raise RequestError(
                "Another account request is still running; try again."
            ) from None

    def close(self) -> None:
        with self.lock:
            if not self.closed:
                self.storage.close()
                self.closed = True
