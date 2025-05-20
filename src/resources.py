from mcp_server import mcp, client
from models import Account, Cash, Position, Order, \
    AccountBucketResultResponse, \
    Exchange, TradeableInstrument, ReportResponse


# ---- MCP Resources ----
@mcp.resource("trading212://account/info")
def get_account_info() -> Account:
    """Fetch account metadata."""
    return client.get_account_info()


@mcp.resource("trading212://account/cash")
def get_account_cash() -> Cash:
    """Fetch account cash balance."""
    return client.get_account_cash()


@mcp.resource("trading212://account/portfolio")
def get_account_positions() -> list[Position]:
    """Fetch all open positions."""
    return client.get_account_positions()


@mcp.resource("trading212://account/portfolio/{ticker}")
def get_account_position_by_ticker(ticker: str) -> Position:
    """Fetch an open position by ticker."""
    return client.get_account_position_by_ticker(ticker)


@mcp.resource("trading212://orders")
def get_orders() -> list[Order]:
    """Fetch current orders."""
    return client.get_orders()


@mcp.resource("trading212://orders/{order_id}")
def get_order_by_id(order_id: int) -> Order:
    """Fetch a specific order by ID."""
    return client.get_order_by_id(order_id)


@mcp.resource("trading212://pies")
def get_pies() -> list[AccountBucketResultResponse]:
    """Fetch all pies."""
    return client.get_pies()


@mcp.resource("trading212://pies/{pie_id}")
def get_pie_by_id(pie_id: int) -> AccountBucketResultResponse:
    """Fetch a specific pie by ID."""
    return client.get_pie_by_id(pie_id)


@mcp.resource("trading212://instruments")
def get_instruments() -> list[TradeableInstrument]:
    """Fetch all tradeable instruments."""
    return client.get_instruments()


@mcp.resource("trading212://exchanges")
def get_exchanges() -> list[Exchange]:
    """Fetch all exchanges and their working schedules."""
    return client.get_exchanges()


@mcp.resource("trading212://history/exports")
def get_reports() -> list[ReportResponse]:
    """Get account export reports."""
    return client.get_reports()
