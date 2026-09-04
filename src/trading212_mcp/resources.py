from collections.abc import Callable

from mcp.server import MCPServer

from .client import Trading212Client
from .models import (
    AccountBucketInstrumentsDetailedResponse,
    AccountBucketResultResponse,
    AccountSummary,
    Cash,
    Exchange,
    Order,
    Position,
    ReportResponse,
    TradeableInstrument,
)
from .registration import safe_handler


def register(mcp: MCPServer, get_client: Callable[[], Trading212Client]) -> None:
    @mcp.resource("trading212://account/info")
    @safe_handler
    def get_account_info() -> AccountSummary:
        """Fetch the account summary."""
        return get_client().get_account_summary()

    @mcp.resource("trading212://account/summary")
    @safe_handler
    def get_account_summary() -> AccountSummary:
        """Fetch the account summary."""
        return get_client().get_account_summary()

    @mcp.resource("trading212://account/cash")
    @safe_handler
    def get_account_cash() -> Cash:
        """Fetch account cash balance."""
        return get_client().get_account_cash()

    @mcp.resource("trading212://account/portfolio")
    @safe_handler
    def get_account_positions() -> list[Position]:
        """Deprecated alias for trading212://positions."""
        return get_client().get_account_positions()

    @mcp.resource("trading212://account/positions")
    @safe_handler
    def get_account_positions_v2() -> list[Position]:
        """Compatibility alias for trading212://positions."""
        return get_client().get_account_positions()

    @mcp.resource("trading212://account/portfolio/{ticker}")
    @safe_handler
    def get_account_position_by_ticker(ticker: str) -> Position:
        """Deprecated alias for trading212://positions/{ticker}."""
        return get_client().get_account_position_by_ticker(ticker)

    @mcp.resource("trading212://account/positions/{ticker}")
    @safe_handler
    def get_account_position_by_ticker_v2(ticker: str) -> Position:
        """Compatibility alias for trading212://positions/{ticker}."""
        return get_client().get_account_position_by_ticker(ticker)

    @mcp.resource("trading212://positions")
    @safe_handler
    def get_positions() -> list[Position]:
        """Fetch all open positions."""
        return get_client().get_positions()

    @mcp.resource("trading212://positions/{ticker}")
    @safe_handler
    def get_position_by_ticker(ticker: str) -> Position:
        """Fetch a single open position by ticker."""
        return get_client().get_account_position_by_ticker(ticker)

    @mcp.resource("trading212://orders")
    @safe_handler
    def get_orders() -> list[Order]:
        """Fetch current orders."""
        return get_client().get_orders()

    @mcp.resource("trading212://orders/{order_id}")
    @safe_handler
    def get_order_by_id(order_id: int) -> Order:
        """Fetch a specific order by ID."""
        return get_client().get_order_by_id(order_id)

    @mcp.resource("trading212://pies")
    @safe_handler
    def get_pies() -> list[AccountBucketResultResponse]:
        """Fetch all pies."""
        return get_client().get_pies()

    @mcp.resource("trading212://pies/{pie_id}")
    @safe_handler
    def get_pie_by_id(pie_id: int) -> AccountBucketInstrumentsDetailedResponse:
        """Fetch a specific pie by ID."""
        return get_client().get_pie_by_id(pie_id)

    @mcp.resource("trading212://instruments")
    @safe_handler
    def get_instruments() -> list[TradeableInstrument]:
        """Fetch all tradeable instruments."""
        return get_client().get_instruments()

    @mcp.resource("trading212://exchanges")
    @safe_handler
    def get_exchanges() -> list[Exchange]:
        """Fetch all exchanges and their working schedules."""
        return get_client().get_exchanges()

    @mcp.resource("trading212://history/exports")
    @safe_handler
    def get_reports() -> list[ReportResponse]:
        """Get account export reports."""
        return get_client().get_reports()
