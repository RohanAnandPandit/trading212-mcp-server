from collections.abc import Callable

from mcp.server import MCPServer

from ..client import Trading212Client
from . import account, history, metadata, orders, pies


def register(mcp: MCPServer, get_client: Callable[[], Trading212Client]) -> None:
    for module in (account, history, metadata, orders, pies):
        module.register(mcp, get_client)
