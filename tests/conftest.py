"""Every API test is offline and uses synthetic credentials."""

from pathlib import Path

import httpx
import pytest

from trading212_mcp.settings import Settings

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def offline(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    for name in (
        "TRADING212_API_KEY",
        "TRADING212_API_SECRET",
        "ENVIRONMENT",
        "TRANSPORT",
    ):
        monkeypatch.delenv(name, raising=False)

    def reject(*args, **kwargs):
        pytest.fail("Live HTTP requests are forbidden in the test suite")

    monkeypatch.setattr(httpx.HTTPTransport, "handle_request", reject)


@pytest.fixture
def settings(tmp_path):
    return Settings(
        api_key="synthetic-key",
        api_secret="synthetic-secret",  # noqa: S106 - intentionally synthetic
        cache_dir=tmp_path / "cache",
    )
