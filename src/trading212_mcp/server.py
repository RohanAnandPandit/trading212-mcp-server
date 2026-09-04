"""Server factory and CLI. Importing never opens an account client."""

import logging
from collections.abc import AsyncIterator, Callable, Iterable
from contextlib import asynccontextmanager
from typing import Any

from mcp.server import MCPServer
from mcp.server.lowlevel.helper_types import ReadResourceContents
from mcp.server.mcpserver import Context
from mcp.server.transport_security import TransportSecuritySettings
from mcp.types import CallToolResult, InputRequiredResult
from pydantic import AnyUrl, ValidationError

from . import __version__, prompts, resources, tools
from .cache import META_KEY, observations
from .client import Trading212Client
from .settings import Settings


class TradingServer(MCPServer[Trading212Client]):
    """Attach per-call freshness metadata after SDK serialization."""

    async def call_tool(
        self,
        name: str,
        arguments: dict[str, Any],
        context: Context[Trading212Client, Any] | None = None,
    ) -> CallToolResult | InputRequiredResult:
        events: list[dict[str, object]] = []
        token = observations.set(events)
        try:
            result = await super().call_tool(name, arguments, context)
            if isinstance(result, CallToolResult) and events:
                result.meta = {**(result.meta or {}), META_KEY: events}
            return result
        finally:
            observations.reset(token)

    async def read_resource(
        self,
        uri: AnyUrl | str,
        context: Context[Trading212Client, Any] | None = None,
    ) -> Iterable[ReadResourceContents] | InputRequiredResult:
        events: list[dict[str, object]] = []
        token = observations.set(events)
        try:
            result = await super().read_resource(uri, context)
            if isinstance(result, InputRequiredResult):
                return result
            contents = list(result)
            for item in contents:
                item.meta = {**(item.meta or {}), META_KEY: events}
            return contents
        finally:
            observations.reset(token)


def create_server(
    settings: Settings | None = None,
    client_factory: Callable[[Settings], Trading212Client] = Trading212Client,
) -> TradingServer:
    active: Trading212Client | None = None

    def current_client() -> Trading212Client:
        if active is None:
            raise RuntimeError("Server lifespan is not running")
        return active

    @asynccontextmanager
    async def lifespan(
        server: MCPServer[Trading212Client],
    ) -> AsyncIterator[Trading212Client]:
        nonlocal active
        client = client_factory(
            settings if settings is not None else Settings.from_env()
        )
        active = client
        try:
            yield client
        finally:
            client.close()
            active = None

    server = TradingServer("Trading212", version=__version__, lifespan=lifespan)
    tools.register(server, current_client)
    resources.register(server, current_client)
    prompts.register(server, current_client)
    return server


def main() -> None:
    logging.basicConfig(
        level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s"
    )
    for name in ("httpx", "httpcore", "hishel"):
        logging.getLogger(name).setLevel(logging.CRITICAL)
    try:
        settings = Settings.from_env()
    except ValidationError:
        raise SystemExit(
            "Invalid configuration. Check API credentials, ENVIRONMENT, TRANSPORT and cache settings."
        ) from None
    server = create_server(settings)
    if settings.transport == "stdio":
        server.run(transport="stdio")
    else:
        server.run(
            transport=settings.transport,
            host="127.0.0.1",
            port=8000,
            transport_security=TransportSecuritySettings(
                enable_dns_rebinding_protection=True,
                allowed_hosts=["127.0.0.1:8000", "localhost:8000"],
                allowed_origins=["http://127.0.0.1:8000", "http://localhost:8000"],
            ),
        )
