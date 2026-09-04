from collections.abc import Callable

from mcp.server import MCPServer

from ..client import Trading212Client
from ..models.account import AccountSummary, Cash, Position
from ..registration import annotations, safe_handler


def register(mcp: MCPServer, get_client: Callable[[], Trading212Client]) -> None:
    @mcp.tool("fetch_account_info", annotations=annotations(write=False))
    @safe_handler
    def fetch_account_info() -> AccountSummary:
        """Fetch the account summary."""
        return get_client().get_account_summary()

    @mcp.tool("fetch_account_summary", annotations=annotations(write=False))
    @safe_handler
    def fetch_account_summary() -> AccountSummary:
        """Fetch the account summary."""
        return get_client().get_account_summary()

    @mcp.tool("fetch_account_cash", annotations=annotations(write=False))
    @safe_handler
    def fetch_account_cash() -> Cash:
        """Fetch account cash balance."""
        return get_client().get_account_cash()

    @mcp.tool("fetch_positions", annotations=annotations(write=False))
    @safe_handler
    def fetch_positions(ticker: str | None = None) -> list[Position]:
        """Fetch open positions, optionally filtered by ticker."""
        return get_client().get_positions(ticker=ticker)

    @mcp.tool("fetch_position_by_ticker", annotations=annotations(write=False))
    @safe_handler
    def fetch_position_by_ticker(ticker: str) -> Position:
        """Fetch a single open position by ticker."""
        return get_client().get_position_by_ticker(ticker)

    @mcp.tool("fetch_all_open_positions", annotations=annotations(write=False))
    @safe_handler
    def fetch_all_open_positions() -> list[Position]:
        """Deprecated alias for fetch_positions()."""
        return get_client().get_account_positions()

    @mcp.tool("fetch_open_position_by_ticker", annotations=annotations(write=False))
    @safe_handler
    def fetch_open_position_by_ticker(ticker: str) -> Position:
        """Deprecated alias for fetch_position_by_ticker()."""
        return get_client().get_account_position_by_ticker(ticker)

    @mcp.tool(
        "search_specific_position_by_ticker", annotations=annotations(write=False)
    )
    @safe_handler
    def search_position_by_ticker(ticker: str) -> Position:
        """Deprecated alias for fetch_position_by_ticker()."""
        return get_client().search_position_by_ticker(ticker)
