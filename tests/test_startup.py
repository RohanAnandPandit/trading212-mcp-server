import asyncio
import importlib.util
import json
import sys
from pathlib import Path

import pytest
from mcp import Client, StdioServerParameters
from pydantic import ValidationError

from trading212_mcp import models
from trading212_mcp.settings import Settings

ROOT = Path(__file__).resolve().parents[1]


def test_model_field_compatibility():
    before = json.loads((ROOT / "tests/fixtures/model_fields_v1.json").read_text())
    for name, shape in before.items():
        model = getattr(models, name)
        assert list(model.model_fields) == shape["fields"], name
        assert [n for n, f in model.model_fields.items() if f.is_required()] == shape[
            "required"
        ], name


def test_import_legacy_launcher_without_credentials(tmp_path):
    spec = importlib.util.spec_from_file_location(
        "legacy_launcher", ROOT / "src/server.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.mcp.name == "Trading212"
    assert not (tmp_path / ".cache").exists()


@pytest.mark.parametrize(
    "args", [["-m", "trading212_mcp"], [str(ROOT / "src/server.py")]]
)
def test_stdio_handshake_discovery_and_shutdown(args, tmp_path):
    async def run():
        async with Client(
            StdioServerParameters(
                command=sys.executable,
                args=args,
                cwd=str(tmp_path),
                env={
                    "TRADING212_API_KEY": "synthetic-stdio",
                    "TRADING212_CACHE_DIR": str(tmp_path / "cache"),
                },
            )
        ) as client:
            result = await client.list_tools()
            assert len(result.tools) == 28
            assert len((await client.list_resources()).resources) == 11
            assert len((await client.list_resource_templates()).resource_templates) == 5
            assert (await client.list_prompts()).prompts[
                0
            ].name == "analyse_trading212_data"

    asyncio.run(run())


@pytest.mark.parametrize(
    "field,value",
    [
        ("environment", "evil"),
        ("transport", "invalid"),
        ("account_ttl", -1),
        ("metadata_ttl", float("inf")),
        ("api_key", ""),
    ],
)
def test_invalid_settings(field, value):
    with pytest.raises(ValidationError):
        Settings.model_validate({"api_key": "synthetic", field: value})


def test_dotenv_only_at_startup_and_env_precedence(monkeypatch, tmp_path):
    (tmp_path / ".env").write_text("TRADING212_API_KEY=file-key\nENVIRONMENT=live\n")
    monkeypatch.setenv("TRADING212_API_KEY", "env-key")
    settings = Settings.from_env()
    assert settings.api_key.get_secret_value() == "env-key"
    assert settings.environment == "live"
    assert "env-key" not in repr(settings)


def test_http_binding_and_protection(monkeypatch):
    from trading212_mcp.server import TradingServer, main

    calls = []
    monkeypatch.setenv("TRADING212_API_KEY", "synthetic-http")
    monkeypatch.setenv("TRANSPORT", "streamable-http")
    monkeypatch.setattr(
        TradingServer, "run", lambda self, **kwargs: calls.append(kwargs)
    )
    main()
    assert calls[0]["host"] == "127.0.0.1"
    protection = calls[0]["transport_security"]
    assert protection.enable_dns_rebinding_protection
    assert "*" not in protection.allowed_hosts
    assert "*" not in protection.allowed_origins


def test_http_rejects_untrusted_host_and_origin(settings):
    import httpx
    from mcp.server.transport_security import TransportSecuritySettings

    from trading212_mcp.server import create_server

    app = create_server(settings).streamable_http_app(
        host="127.0.0.1",
        transport_security=TransportSecuritySettings(
            enable_dns_rebinding_protection=True,
            allowed_hosts=["127.0.0.1:8000", "localhost:8000"],
            allowed_origins=["http://127.0.0.1:8000", "http://localhost:8000"],
        ),
    )

    async def run():
        async with app.router.lifespan_context(app):
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app),
                base_url="http://127.0.0.1:8000",
                trust_env=False,
            ) as client:
                bad_host = await client.post(
                    "/mcp", headers={"host": "evil.invalid"}, json={}
                )
                assert bad_host.status_code == 421
                bad_origin = await client.post(
                    "/mcp", headers={"origin": "https://evil.invalid"}, json={}
                )
                assert bad_origin.status_code == 403

    asyncio.run(run())
