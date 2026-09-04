import os
import stat
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from contextlib import ExitStack
from dataclasses import dataclass, field
from threading import Barrier, Event

import hishel
import httpx
import pytest

from utils.client import Trading212Client
from utils.hishel_config import controller, create_storage


@dataclass
class CacheTestHarness:
    """Named controls and observations for the real clients under test."""

    calls: list[httpx.Request] = field(default_factory=list)
    storages: list[hishel.FileStorage] = field(default_factory=list)
    status_code: int = 200
    fail_requests: bool = False

    def create(
        self,
        key: str = "synthetic-key-a",
        secret: str | None = "synthetic-secret-a",
        *,
        environment: str | None = None,
        version: str = "v0",
    ) -> hishel.CacheClient:
        return Trading212Client(
            api_key=key,
            api_secret=secret,
            environment=environment,
            version=version,
        ).client

    def respond(self, request: httpx.Request) -> httpx.Response:
        self.calls.append(request)
        if self.fail_requests:
            raise httpx.ConnectError(
                "Synthetic connection failure", request=request
            )
        return httpx.Response(
            self.status_code,
            json={
                "account": request.headers["Authorization"],
                "url": str(request.url),
                "call": len(self.calls),
            },
        )


@pytest.fixture
def clients(tmp_path, monkeypatch):
    """Use real cache clients and storage, with no real HTTP requests."""
    monkeypatch.chdir(tmp_path)
    for name in ("TRADING212_API_KEY", "TRADING212_API_SECRET", "ENVIRONMENT"):
        monkeypatch.delenv(name, raising=False)
    # Also lets the isolation regression exercise the original shared storage.
    (tmp_path / ".cache/hishel").mkdir(parents=True)
    original_client = hishel.CacheClient
    harness = CacheTestHarness()

    def reject_network(*args, **kwargs):
        pytest.fail("Tests must not make real network requests")

    monkeypatch.setattr(httpx.HTTPTransport, "handle_request", reject_network)
    with ExitStack() as stack:
        def cache_client(**kwargs):
            harness.storages.append(kwargs["storage"])
            return stack.enter_context(original_client(
                **kwargs,
                transport=httpx.MockTransport(harness.respond),
                trust_env=False,
            ))

        monkeypatch.setattr(hishel, "CacheClient", cache_client)

        yield harness


@pytest.mark.parametrize("credentials", [
    [("synthetic-key-a", "secret-a"), ("synthetic-key-b", "secret-b")],
    [("synthetic-key-a", "secret-a"), ("synthetic-key-a", "secret-b")],
    [("legacy-key-a", None), ("legacy-key-b", None)],
    [("synthetic-key-a", None), ("synthetic-key-a", "secret-a")],
])
def test_credentials_never_share_responses(clients, credentials):
    account_clients = [clients.create(key, secret) for key, secret in credentials]
    for client in account_clients:
        response = client.get("/equity/account/summary")
        assert response.json()["account"] == client.headers["Authorization"]
        assert response.extensions["from_cache"] is False
    for client in account_clients:
        response = client.get("/equity/account/summary")
        assert response.json()["account"] == client.headers["Authorization"]
        assert response.extensions["from_cache"] is True
    assert len(clients.calls) == 2


def test_identical_credentials_reuse_persistent_cache(clients):
    first = clients.create()
    response = first.get("/equity/account/summary")
    first.close()
    second = clients.create()
    cached = second.get("/equity/account/summary")
    assert cached.json() == response.json()
    assert cached.extensions["from_cache"] is True
    assert len(clients.calls) == 1
    assert clients.storages[0] is clients.storages[1]


def test_concurrent_clients_wait_for_complete_cache_writes(clients, monkeypatch):
    first, second = clients.create(), clients.create()
    writer_storage, reader_storage = clients.storages
    write_started, release_write, read_started = Event(), Event(), Event()

    def paused_write(path, data, is_binary=None):
        # Pause after flushing partial JSON, while Hishel holds its write lock.
        with open(path, "w", encoding="utf-8") as output:
            output.write("{")
            output.flush()
            write_started.set()
            assert release_write.wait(5)
            output.seek(0)
            output.write(data)
            output.truncate()

    monkeypatch.setattr(writer_storage._file_manager, "write_to", paused_write)
    with ThreadPoolExecutor(max_workers=2) as pool:
        writer = pool.submit(first.get, "/equity/account/summary")
        try:
            assert write_started.wait(5)
            original_retrieve = reader_storage.retrieve

            def observed_retrieve(key):
                read_started.set()
                return original_retrieve(key)

            monkeypatch.setattr(reader_storage, "retrieve", observed_retrieve)
            reader = pool.submit(second.get, "/equity/account/summary")
            assert read_started.wait(5)
            with pytest.raises(TimeoutError):
                reader.result(timeout=0.1)
        finally:
            release_write.set()
        written = writer.result(timeout=5)
        cached = reader.result(timeout=5)

    assert cached.json() == written.json()
    assert cached.extensions["from_cache"] is True
    assert len(clients.calls) == 1


def test_concurrent_storage_creation_shares_one_instance(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    barrier = Barrier(8)

    def create(_):
        barrier.wait(timeout=5)
        return create_storage("https://demo.trading212.com/api/v0", "test-key")

    with ThreadPoolExecutor(max_workers=8) as pool:
        storages = list(pool.map(create, range(8)))
    assert all(storage is storages[0] for storage in storages)


def test_environments_and_versions_have_separate_namespaces(clients):
    targets = (("demo", "v0"), ("live", "v0"), ("demo", "v1"))
    for environment, version in targets:
        client = clients.create(environment=environment, version=version)
        response = client.get("/equity/account/summary")
        assert response.extensions["from_cache"] is False
        assert response.json()["url"].startswith(
            f"https://{environment}.trading212.com/api/{version}/"
        )
    assert len({storage._base_path for storage in clients.storages}) == 3
    assert len(clients.calls) == 3


def test_legacy_shared_cache_is_ignored(clients, tmp_path):
    legacy_storage = hishel.FileStorage(
        base_path=tmp_path / ".cache/hishel", ttl=300
    )
    legacy = hishel.CacheClient(
        base_url="https://demo.trading212.com/api/v0",
        headers={"Authorization": "synthetic-legacy-account"},
        storage=legacy_storage,
        controller=controller,
    )
    legacy.get("/equity/account/summary")
    assert legacy.get("/equity/account/summary").extensions["from_cache"]
    legacy.close()
    client = clients.create()
    response = client.get("/equity/account/summary")
    assert response.json()["account"] == client.headers["Authorization"]
    assert response.extensions["from_cache"] is False
    assert len(clients.calls) == 2
    assert any(
        path.name != ".gitignore"
        for path in legacy_storage._base_path.iterdir()
    )


def test_expired_entries_are_refetched(clients):
    client = clients.create()
    client.get("/equity/account/summary")
    for path in clients.storages[0]._base_path.iterdir():
        if path.name != ".gitignore":
            os.utime(path, (0, 0))
    response = client.get("/equity/account/summary")
    assert response.extensions["from_cache"] is False
    assert response.json()["call"] == 2
    assert len(clients.calls) == 2


@pytest.mark.parametrize("method,status", [
    ("POST", 200), ("DELETE", 200), ("GET", 201),
    ("GET", 401), ("GET", 429), ("GET", 500),
])
def test_only_successful_gets_are_cached(clients, method, status):
    clients.status_code = status
    client = clients.create()
    for _ in range(2):
        response = client.request(method, "/equity/orders")
        assert response.status_code == status
        assert not response.extensions.get("from_cache", False)
    assert len(clients.calls) == 2


def test_namespace_is_hashed_private_and_repeatable(clients):
    client = clients.create()
    clients.create()
    path = clients.storages[0]._base_path
    assert path.parent.name == "trading212-v2"
    assert len(path.name) == 64
    assert set(path.name) <= set("0123456789abcdef")
    for value in (
        "synthetic-key-a", "synthetic-secret-a", client.headers["Authorization"]
    ):
        assert value not in str(path)
    assert path == clients.storages[1]._base_path
    if os.name == "posix":
        assert stat.S_IMODE(path.stat().st_mode) == 0o700


def test_connection_failure_cannot_fall_back_to_another_account(clients):
    clients.create().get("/equity/account/summary")
    other = clients.create("synthetic-key-b", "synthetic-secret-b")
    clients.fail_requests = True
    with pytest.raises(httpx.ConnectError):
        other.get("/equity/account/summary")
