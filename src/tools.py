from src.mcp_server import mcp, client

from src.models import (Account, Cash, Position, Order,
                        AccountBucketResultResponse,
                        Exchange, TradeableInstrument, HistoricalOrder,
                        LimitRequest, MarketRequest, StopLimitRequest)


@mcp.tool("get_account_info")
def get_account_info() -> Account:
    """Fetch account metadata."""
    return client.get_account_info()


@mcp.tool("get_account_cash")
def get_account_cash() -> Cash:
    """Fetch account cash balance."""
    return client.get_account_cash()


@mcp.tool("get_account_positions")
def get_account_positions() -> list[Position]:
    """Fetch all open positions."""
    return client.get_account_positions()


@mcp.tool("get_account_position_by_ticker")
def get_account_position_by_ticker(ticker: str) -> Position:
    """Fetch a position by ticker (deprecated)."""
    return client.get_account_position_by_ticker(ticker)


@mcp.tool("search_position_by_ticker")
def search_position_by_ticker(ticker: str) -> Position:
    """Search for a position by ticker using the POST endpoint."""
    return client.search_position_by_ticker(ticker)


@mcp.tool("get_orders")
def get_orders() -> list[Order]:
    """Fetch current orders."""
    return client.get_orders()


@mcp.tool("get_pies")
def get_pies() -> list[AccountBucketResultResponse]:
    """Fetch all pies."""
    return client.get_pies()


@mcp.tool("get_history_orders")
def get_history_orders(cursor: int = None, ticker: str = None,
                       limit: int = 20) -> list[HistoricalOrder]:
    """Fetch historical order data with pagination."""
    return client.get_history_orders(cursor=cursor, ticker=ticker, limit=limit)


@mcp.tool("get_instruments")
def get_instruments() -> list[TradeableInstrument]:
    """Fetch all tradeable instruments."""
    return client.get_instruments()


@mcp.tool("get_exchanges")
def get_exchanges() -> list[Exchange]:
    """Fetch all exchanges and their working schedules."""
    return client.get_exchanges()


@mcp.tool("place_market_order")
def place_market_order(market_request: MarketRequest) -> Order:
    """Place a market order."""
    return client.place_market_order(market_request)


@mcp.tool("place_limit_order")
def place_limit_order(limit_request: LimitRequest) -> Order:
    """Place a limit order."""
    return client.place_limit_order(limit_request)


@mcp.tool("place_stop_limit_order")
def place_stop_limit_order(stop_limit_request: StopLimitRequest) -> Order:
    """Place a stop-limit order."""
    return client.place_stop_limit_order(stop_limit_request)


@mcp.tool("cancel_order")
def cancel_order(order_id: int) -> None:
    """Cancel an existing order."""
    client.cancel_order(order_id)


@mcp.tool("duplicate_pie")
def duplicate_pie(pie_id: int) -> AccountBucketResultResponse:
    """Duplicate a pie."""
    return client.duplicate_pie(pie_id)


@mcp.tool("delete_pie")
def delete_pie(pie_id: int) -> None:
    """Delete a pie."""
    client.delete_pie(pie_id)


@mcp.tool("get_reports")
def get_reports() -> list[dict]:
    """Get account export reports."""
    return client.get_reports()
