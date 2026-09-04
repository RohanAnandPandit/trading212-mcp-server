import os
import stat
from contextlib import ExitStack

import hishel
import httpx
import pytest

from utils.client import Trading212Client
from utils.hishel_config import controller


@pytest.fixture
def clients(tmp_path, monkeypatch):
    """Use real cache clients and storage, with no real HTTP requests."""
    monkeypatch.chdir(tmp_path)
    for name in ("TRADING212_API_KEY", "TRADING212_API_SECRET", "ENVIRONMENT"):
        monkeypatch.delenv(name, raising=False)
    # Also lets the isolation regression exercise the original shared storage.
    (tmp_path / ".cache/hishel").mkdir(parents=True)
    original_client = hishel.CacheClient
    calls = []
    storages = []
    state = {"status": 200, "fail": False}

    def respond(request):
        calls.append(request)
        if state["fail"]:
            raise httpx.ConnectError(
                "Synthetic connection failure", request=request
            )
        return httpx.Response(
            state["status"],
            json={
                "account": request.headers["Authorization"],
                "url": str(request.url),
                "call": len(calls),
            },
        )

    def reject_network(*args, **kwargs):
        pytest.fail("Tests must not make real network requests")

    monkeypatch.setattr(httpx.HTTPTransport, "handle_request", reject_network)
    with ExitStack() as stack:
        def cache_client(**kwargs):
            storages.append(kwargs["storage"])
            return stack.enter_context(original_client(
                **kwargs,
                transport=httpx.MockTransport(respond),
                trust_env=False,
            ))

        monkeypatch.setattr(hishel, "CacheClient", cache_client)

        def create(
            key="synthetic-key-a", secret="synthetic-secret-a", **kwargs
        ):
            return Trading212Client(
                api_key=key, api_secret=secret, **kwargs
            ).client

        yield create, calls, storages, state


@pytest.mark.parametrize("credentials", [
    [("synthetic-key-a", "secret-a"), ("synthetic-key-b", "secret-b")],
    [("synthetic-key-a", "secret-a"), ("synthetic-key-a", "secret-b")],
    [("legacy-key-a", None), ("legacy-key-b", None)],
    [("synthetic-key-a", None), ("synthetic-key-a", "secret-a")],
])
def test_credentials_never_share_responses(clients, credentials):
    create, calls, _, _ = clients
    account_clients = [create(key, secret) for key, secret in credentials]
    for client in account_clients:
        response = client.get("/equity/account/summary")
        assert response.json()["account"] == client.headers["Authorization"]
        assert response.extensions["from_cache"] is False
    for client in account_clients:
        response = client.get("/equity/account/summary")
        assert response.json()["account"] == client.headers["Authorization"]
        assert response.extensions["from_cache"] is True
    assert len(calls) == 2


def test_identical_credentials_reuse_persistent_cache(clients):
    create, calls, storages, _ = clients
    first = create()
    response = first.get("/equity/account/summary")
    first.close()
    second = create()
    cached = second.get("/equity/account/summary")
    assert cached.json() == response.json()
    assert cached.extensions["from_cache"] is True
    assert len(calls) == 1
    assert storages[0] is not storages[1]
    assert storages[0]._base_path == storages[1]._base_path


def test_environments_and_versions_have_separate_namespaces(clients):
    create, calls, storages, _ = clients
    targets = (("demo", "v0"), ("live", "v0"), ("demo", "v1"))
    for environment, version in targets:
        client = create(environment=environment, version=version)
        response = client.get("/equity/account/summary")
        assert response.extensions["from_cache"] is False
        assert response.json()["url"].startswith(
            f"https://{environment}.trading212.com/api/{version}/"
        )
    assert len({storage._base_path for storage in storages}) == 3
    assert len(calls) == 3


def test_legacy_shared_cache_is_ignored(clients, tmp_path):
    create, calls, _, _ = clients
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
    client = create()
    response = client.get("/equity/account/summary")
    assert response.json()["account"] == client.headers["Authorization"]
    assert response.extensions["from_cache"] is False
    assert len(calls) == 2
    assert any(
        path.name != ".gitignore"
        for path in legacy_storage._base_path.iterdir()
    )


def test_expired_entries_are_refetched(clients):
    create, calls, storages, _ = clients
    client = create()
    client.get("/equity/account/summary")
    for path in storages[0]._base_path.iterdir():
        if path.name != ".gitignore":
            os.utime(path, (0, 0))
    response = client.get("/equity/account/summary")
    assert response.extensions["from_cache"] is False
    assert response.json()["call"] == 2
    assert len(calls) == 2


@pytest.mark.parametrize("method,status", [
    ("POST", 200), ("DELETE", 200), ("GET", 201),
    ("GET", 401), ("GET", 429), ("GET", 500),
])
def test_only_successful_gets_are_cached(clients, method, status):
    create, calls, _, state = clients
    state["status"] = status
    client = create()
    for _ in range(2):
        response = client.request(method, "/equity/orders")
        assert response.status_code == status
        assert not response.extensions.get("from_cache", False)
    assert len(calls) == 2


def test_namespace_is_hashed_private_and_repeatable(clients):
    create, _, storages, _ = clients
    client = create()
    create()
    path = storages[0]._base_path
    assert path.parent.name == "trading212-v2"
    assert len(path.name) == 64
    assert set(path.name) <= set("0123456789abcdef")
    for value in (
        "synthetic-key-a", "synthetic-secret-a", client.headers["Authorization"]
    ):
        assert value not in str(path)
    assert path == storages[1]._base_path
    if os.name == "posix":
        assert stat.S_IMODE(path.stat().st_mode) == 0o700


def test_connection_failure_cannot_fall_back_to_another_account(clients):
    create, _, _, state = clients
    create().get("/equity/account/summary")
    other = create("synthetic-key-b", "synthetic-secret-b")
    state["fail"] = True
    with pytest.raises(httpx.ConnectError):
        other.get("/equity/account/summary")
