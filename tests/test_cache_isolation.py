import base64
import os
import stat
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from threading import Event

import httpx
import pytest

from trading212_mcp.cache import observations
from trading212_mcp.client import Trading212Client
from trading212_mcp.errors import UpstreamError
from trading212_mcp.settings import Settings

PATH = "/equity/orders"


def client(settings, calls):
    def respond(req):
        calls.append(req)
        return httpx.Response(
            200,
            json={"count": len(calls)},
            headers={"set-cookie": "session=synthetic-cookie"},
        )

    return Trading212Client(settings, transport=httpx.MockTransport(respond))


@pytest.mark.parametrize(
    "keys",
    [
        [("key-a", "secret-a"), ("key-b", "secret-b")],
        [("key-a", "secret-a"), ("key-a", "secret-b")],
        [("key-a", None), ("key-b", None)],
        [("key-a", None), ("key-a", "secret-a")],
    ],
)
def test_credentials_never_share_responses(settings, keys):
    calls = []
    for key, secret in keys:
        cfg = Settings.model_validate(
            {**settings.model_dump(), "api_key": key, "api_secret": secret}
        )
        with client(cfg, calls) as c:
            first = c._make_request("GET", PATH)
            assert first == c._make_request("GET", PATH)
    assert len(calls) == 2


def test_restart_reuses_cache_and_close_is_independent(settings):
    calls = []
    first = client(settings, calls)
    second = client(settings, calls)
    original = first._make_request("GET", PATH)
    first.close()
    assert second._make_request("GET", PATH) == original
    second.close()
    with client(settings, calls) as restarted:
        assert restarted._make_request("GET", PATH) == original
    assert len(calls) == 1


def test_private_files_never_contain_credentials(settings):
    calls = []
    with client(settings, calls) as c:
        c._make_request("GET", PATH)
        path = c.cache.path
    assert (
        calls[0].headers["Authorization"]
        == "Basic " + base64.b64encode(b"synthetic-key:synthetic-secret").decode()
    )
    for file in path.rglob("*"):
        if file.is_file():
            data = file.read_bytes()
            for secret in (
                b"synthetic-key",
                b"synthetic-secret",
                b"Authorization",
                b"synthetic-cookie",
                calls[0].headers["Authorization"].encode(),
            ):
                assert secret not in data
            if os.name == "posix" and file.name != ".gitignore":
                assert stat.S_IMODE(file.stat().st_mode) == 0o600
    if os.name == "posix":
        assert stat.S_IMODE(path.stat().st_mode) == 0o700


def test_environment_and_version_isolation(settings):
    calls = []
    for env, version in [("demo", "v0"), ("live", "v0"), ("demo", "v1")]:
        cfg = settings.model_copy(update={"environment": env})
        with Trading212Client(
            cfg,
            version=version,
            transport=httpx.MockTransport(
                lambda req: calls.append(req) or httpx.Response(200, json={})
            ),
        ) as c:
            c._make_request("GET", PATH)
    assert len(calls) == 3
    assert len({str(req.url) for req in calls}) == 3


def test_expiration_and_no_sliding_ttl(settings):
    calls = []
    with client(settings, calls) as c:
        c._make_request("GET", PATH)
        # Advance Hishel's clock, without sleeps or depending on its SQL schema.
        import time
        from unittest.mock import patch

        with patch(
            "hishel._core._storages._sync_sqlite.time.time",
            return_value=time.time() + 16,
        ):
            c._make_request("GET", PATH)
    assert len(calls) == 2


@pytest.mark.parametrize(
    ("ttl_setting", "path"),
    [
        ("account_ttl", PATH),
        ("history_ttl", "/equity/history/orders"),
        ("metadata_ttl", "/equity/metadata/instruments"),
    ],
)
@pytest.mark.parametrize("restart", [False, True])
def test_reduced_ttl_applies_to_persisted_entries(
    settings, monkeypatch, ttl_setting, path, restart
):
    import time

    calls = []
    long_lived = settings.model_copy(update={ttl_setting: 3600})
    short_lived = settings.model_copy(update={ttl_setting: 15})
    with client(long_lived, calls) as original:
        assert original._make_request("GET", path) == {"count": 1}
        if restart:
            original.close()
        future = time.time() + 60
        monkeypatch.setattr("trading212_mcp.cache.time.time", lambda: future)
        events = []
        token = observations.set(events)
        try:
            with client(short_lived, calls) as current:
                assert current._make_request("GET", path) == {"count": 2}
        finally:
            observations.reset(token)
        assert events[0]["cacheHit"] is False
        assert events[0]["ttlSeconds"] == 15
    assert len(calls) == 2


@pytest.mark.parametrize("method", ["POST", "DELETE"])
def test_mutations_invalidate_private_but_not_metadata(settings, method):
    calls = []
    with client(settings, calls) as c:
        c._make_request("GET", PATH)
        metadata = c._make_request("GET", "/equity/metadata/instruments")
        c._make_request(method, PATH)
        assert c._make_request("GET", PATH)["count"] == 4
        assert c._make_request("GET", "/equity/metadata/instruments") == metadata
        c._make_request(method, PATH)
    assert len(calls) == 5


def test_uncertain_mutation_invalidates_without_retry(settings):
    calls = []

    def respond(req):
        calls.append(req)
        if req.method == "POST":
            raise httpx.ReadTimeout("SYNTHETIC SENSITIVE DETAIL")
        return httpx.Response(200, json={"call": len(calls)})

    with Trading212Client(settings, transport=httpx.MockTransport(respond)) as c:
        c._make_request("GET", PATH)
        with pytest.raises(UpstreamError, match="outcome may be unknown"):
            c._make_request("POST", PATH)
        assert c._make_request("GET", PATH) == {"call": 3}
    assert [r.method for r in calls] == ["GET", "POST", "GET"]


def test_concurrent_read_cannot_repopulate_old_generation(settings):
    started, release = Event(), Event()
    calls = []

    def respond(req):
        calls.append(req.method)
        if len(calls) == 1:
            started.set()
            assert release.wait(5)
        return httpx.Response(200, json={"call": len(calls)})

    with (
        Trading212Client(settings, transport=httpx.MockTransport(respond)) as a,
        Trading212Client(settings, transport=httpx.MockTransport(respond)) as b,
        ThreadPoolExecutor(2) as pool,
    ):
        read = pool.submit(a._make_request, "GET", PATH)
        assert started.wait(5)
        write = pool.submit(b._make_request, "POST", PATH)
        try:
            with pytest.raises(TimeoutError):
                write.result(timeout=0.1)
        finally:
            release.set()
        read.result(timeout=5)
        write.result(timeout=5)
        assert a._make_request("GET", PATH) == {"call": 3}


def test_same_account_concurrent_clients_share_cache(settings):
    calls = []
    with ThreadPoolExecutor(8) as pool:

        def fetch(_):
            with client(settings, calls) as c:
                return c._make_request("GET", PATH)

        results = list(pool.map(fetch, range(8)))
    assert results == [{"count": 1}] * 8
    assert len(calls) == 1


def test_freshness_metadata(settings):
    calls = []
    events = []
    token = observations.set(events)
    try:
        with client(settings, calls) as c:
            c._make_request("GET", PATH)
            c._make_request("GET", PATH)
        assert [e["cacheHit"] for e in events] == [False, True]
        assert events[0]["retrievedAt"] == events[1]["retrievedAt"]
        assert events[0]["ttlSeconds"] == 15
    finally:
        observations.reset(token)


def test_zero_ttl_disables_cache(settings):
    calls = []
    with client(settings.model_copy(update={"account_ttl": 0}), calls) as c:
        c._make_request("GET", PATH)
        c._make_request("GET", PATH)
    assert len(calls) == 2


def test_legacy_cache_is_ignored(settings, tmp_path):
    legacy = tmp_path / ".cache/trading212-v2/legacy"
    legacy.mkdir(parents=True)
    (legacy / "data").write_text("synthetic-private-data")
    calls = []
    with client(settings, calls) as c:
        c._make_request("GET", PATH)
    assert len(calls) == 1 and (legacy / "data").exists()


def process_read(cache_dir, counter, barrier, results):
    """Spawn-safe worker; no inherited clients or database connections."""
    cfg = Settings(api_key="synthetic-process", cache_dir=cache_dir)

    def respond(req):
        with counter.get_lock():
            counter.value += 1
            value = counter.value
        return httpx.Response(200, json={"call": value})

    with Trading212Client(cfg, transport=httpx.MockTransport(respond)) as c:
        barrier.wait(timeout=10)
        results.put(c._make_request("GET", PATH))


def test_cross_process_cache_coordination(tmp_path):
    import multiprocessing

    ctx = multiprocessing.get_context("spawn")
    counter, barrier, results = ctx.Value("i", 0), ctx.Barrier(2), ctx.Queue()
    workers = [
        ctx.Process(target=process_read, args=(tmp_path, counter, barrier, results))
        for _ in range(2)
    ]
    try:
        for worker in workers:
            worker.start()
        assert [results.get(timeout=15) for _ in workers] == [{"call": 1}] * 2
        for worker in workers:
            worker.join(timeout=10)
            assert worker.exitcode == 0
        assert counter.value == 1
    finally:
        for worker in workers:
            if worker.is_alive():
                worker.terminate()
                worker.join()
        results.close()
        results.join_thread()


def test_connection_failure_never_uses_other_account(settings):
    calls = []
    with client(settings, calls) as first:
        first._make_request("GET", PATH)
    cfg = Settings.model_validate(
        {**settings.model_dump(), "api_key": "another-synthetic-key"}
    )

    def fail(req):
        raise httpx.ConnectError("synthetic-network-failure")

    with Trading212Client(
        cfg, transport=httpx.MockTransport(fail), sleep=lambda _: None
    ) as other:
        with pytest.raises(UpstreamError):
            other._make_request("GET", PATH)
