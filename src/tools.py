from typing import Optional, Union
from mcp_server import mcp, registry

from models import *
from utils.response import format_response


# Instruments Metadata
@mcp.tool("search_instrument")
def search_instrument(
    search_term: str = None,
    account: Union[str, list[str], None] = None,
) -> list[TradeableInstrument]:
    """
    Fetch instruments, optionally filtered by ticker or name.

    Args:
        search_term: Search term to filter instruments by ticker or name (case-insensitive)
        account: Account name or None for the default account. Instrument data
            is market-wide; any account's credentials work. Multi-account input
            (list or "all") is not allowed for this tool.

    Returns:
        List of matching TradeableInstrument objects, or all instruments if no
        search term is provided
    """
    clients = registry.resolve(account)
    if len(clients) > 1:
        raise ValueError(
            "search_instrument returns market-wide data; "
            "specify a single account name or None for the default."
        )
    client = next(iter(clients.values()))
    instruments = client.get_instruments()

    if not search_term:
        return instruments

    search_lower = search_term.lower()
    return [
        inst
        for inst in instruments
        if (inst.ticker and search_lower in inst.ticker.lower())
        or (inst.name and search_lower in inst.name.lower())
    ]


@mcp.tool("search_exchange")
def search_exchange(
    search_term: str = None,
    account: Union[str, list[str], None] = None,
) -> list[Exchange]:
    """
    Fetch exchanges, optionally filtered by name or ID.

    Args:
        search_term: Optional search term to filter exchanges by name or ID (case-insensitive)
        account: Account name or None for the default account. Exchange data
            is market-wide; any account's credentials work. Multi-account input
            (list or "all") is not allowed for this tool.

    Returns:
        List of matching Exchange objects, or all exchanges if no search term is provided
    """
    clients = registry.resolve(account)
    if len(clients) > 1:
        raise ValueError(
            "search_exchange returns market-wide data; "
            "specify a single account name or None for the default."
        )
    client = next(iter(clients.values()))
    exchanges = client.get_exchanges()

    if not search_term:
        return exchanges

    search_lower = search_term.lower()
    return [
        exch
        for exch in exchanges
        if (exch.name and search_lower in exch.name.lower())
        or (str(exch.id) == search_term)
    ]


# Pies
@mcp.tool("fetch_pies")
def fetch_pies(account: Union[str, list[str], None] = None):
    """
    Fetch all pies.

    Args:
        account: Account name, list of names, "all", or None for default account.
    """
    clients = registry.resolve(account)
    results = {}
    for name, c in clients.items():
        try:
            results[name] = c.get_pies()
        except Exception as e:
            results[name] = e
    return format_response(results)


@mcp.tool("create_pie")
def create_pie(
    name: str,
    instrument_shares: dict[str, float],
    account: str,
    dividend_cash_action: Optional[DividendCashActionEnum] = None,
    end_date: Optional[datetime] = None,
    goal: Optional[float] = None,
    icon: Optional[str] = None,
) -> AccountBucketInstrumentsDetailedResponse:
    """
    Create a new pie with the specified parameters.

    Args:
        name: Name of the pie
        instrument_shares: Dictionary mapping instrument tickers to their
        weights in the pie (e.g., {'AAPL_US_EQ': 0.5, 'MSFT_US_EQ': 0.5})
        account: Account name to create the pie in (required)
        dividend_cash_action: How dividends are handled. Defaults to REINVEST.
            Possible values: REINVEST, TO_ACCOUNT_CASH
        end_date: Optional end date for the pie in ISO 8601 format
            (e.g., '2024-12-31T23:59:59Z')
        goal: Total desired value of the pie in account currency
        icon: Optional icon identifier for the pie

    Returns:
        AccountBucketInstrumentsDetailedResponse: Details of the created pie
    """
    client = registry.get_client(account)
    pie_data = PieRequest(
        name=name,
        instrumentShares=instrument_shares,
        dividendCashAction=dividend_cash_action,
        endDate=end_date,
        goal=goal,
        icon=icon,
    )
    return client.create_pie(pie_data)


@mcp.tool("delete_pie")
def delete_pie(pie_id: int, account: str):
    """
    Delete a pie.

    Args:
        pie_id: ID of the pie to delete
        account: Account name that owns the pie (required)
    """
    return registry.get_client(account).delete_pie(pie_id)


@mcp.tool("fetch_a_pie")
def fetch_a_pie(pie_id: int, account: Union[str, list[str], None] = None):
    """
    Fetch a specific pie by ID.

    Args:
        pie_id: ID of the pie to fetch
        account: Account name, list of names, "all", or None for default account.
    """
    clients = registry.resolve(account)
    results = {}
    for name, c in clients.items():
        try:
            results[name] = c.get_pie_by_id(pie_id)
        except Exception as e:
            results[name] = e
    return format_response(results)


@mcp.tool("update_pie")
def update_pie(
    pie_id: int,
    account: str,
    name: str = None,
    instrument_shares: dict[str, float] = None,
    dividend_cash_action: Optional[DividendCashActionEnum] = None,
    end_date: Optional[datetime] = None,
    goal: Optional[float] = None,
    icon: Optional[str] = None,
) -> AccountBucketInstrumentsDetailedResponse:
    """
    Update an existing pie with new parameters. The pie must be renamed when
    updating it.

    Args:
        pie_id: ID of the pie to update
        account: Account name that owns the pie (required)
        name: New name for the pie. Required when updating a pie.
        instrument_shares: Dictionary mapping instrument tickers to their new
        weights in the pie (e.g., {'AAPL_US_EQ': 0.5, 'MSFT_US_EQ': 0.5})
        dividend_cash_action: How dividends should be handled.
            Possible values: REINVEST, TO_ACCOUNT_CASH
        end_date: New end date for the pie in ISO 8601 format
        goal: New total desired value of the pie in account currency
        icon: New icon identifier for the pie

    Returns:
        AccountBucketInstrumentsDetailedResponse: Updated details of the pie
    """
    client = registry.get_client(account)
    pie_data = PieRequest(
        name=name,
        instrumentShares=instrument_shares,
        dividendCashAction=dividend_cash_action,
        endDate=end_date,
        goal=goal,
        icon=icon,
    )
    return client.update_pie(pie_id, pie_data)


@mcp.tool("duplicate_pie")
def duplicate_pie(
    pie_id: int,
    account: str,
    name: Optional[str] = None,
    icon: Optional[str] = None,
) -> AccountBucketResultResponse:
    """
    Create a duplicate of an existing pie.

    Args:
        pie_id: ID of the pie to duplicate
        account: Account name that owns the pie (required)
        name: Optional new name for the duplicated pie
        icon: Optional new icon for the duplicated pie

    Returns:
        AccountBucketResultResponse: Details of the duplicated pie
    """
    duplicate_request = DuplicateBucketRequest(name=name, icon=icon)
    return registry.get_client(account).duplicate_pie(pie_id, duplicate_request)


# Equity Orders
@mcp.tool("fetch_all_orders")
def fetch_orders(account: Union[str, list[str], None] = None):
    """
    Fetch all equity orders.

    Args:
        account: Account name, list of names, "all", or None for default account.
    """
    clients = registry.resolve(account)
    results = {}
    for name, c in clients.items():
        try:
            results[name] = c.get_orders()
        except Exception as e:
            results[name] = e
    return format_response(results)


@mcp.tool("place_limit_order")
def place_limit_order(
    ticker: str,
    quantity: float,
    limit_price: float,
    account: str,
    time_validity: LimitRequestTimeValidityEnum = LimitRequestTimeValidityEnum.DAY,
) -> Order:
    """
    Place a limit order to buy or sell an instrument at a specified price or better.

    Args:
        ticker: Ticker symbol of the instrument to trade (e.g., 'AAPL_US_EQ')
        quantity: Number of shares/units to trade
        limit_price: Limit price for the order
        account: Account name to place the order in (required)
        time_validity: Time validity of the order. Defaults to DAY.
            Possible values: DAY, GOOD_TILL_CANCEL

    Returns:
        Order: Details of the placed order
    """
    limit_request = LimitRequest(
        ticker=ticker,
        quantity=quantity,
        limitPrice=limit_price,
        timeValidity=time_validity,
    )
    return registry.get_client(account).place_limit_order(limit_request)


@mcp.tool("place_market_order")
def place_market_order(ticker: str, quantity: float, account: str) -> Order:
    """
    Place a market order to buy or sell an instrument at the current market price.

    Args:
        ticker: Ticker symbol of the instrument to trade (e.g., 'AAPL_US_EQ')
        quantity: Number of shares/units to trade
        account: Account name to place the order in (required)

    Returns:
        Order: Details of the placed order
    """
    market_request = MarketRequest(ticker=ticker, quantity=quantity)
    return registry.get_client(account).place_market_order(market_request)


@mcp.tool("place_stop_order")
def place_stop_order(
    ticker: str,
    quantity: float,
    stop_price: float,
    account: str,
    time_validity: StopRequestTimeValidityEnum = StopRequestTimeValidityEnum.DAY,
) -> Order:
    """
    Place a stop order to buy or sell an instrument when the market price
    reaches a specified stop price.

    Args:
        ticker: Ticker symbol of the instrument to trade (e.g., 'AAPL_US_EQ')
        quantity: Number of shares/units to trade
        stop_price: Stop price that triggers the order
        account: Account name to place the order in (required)
        time_validity: Time validity of the order. Defaults to DAY.
            Possible values: DAY, GOOD_TILL_CANCEL

    Returns:
        Order: Details of the placed order
    """
    stop_request = StopRequest(
        ticker=ticker,
        quantity=quantity,
        stopPrice=stop_price,
        timeValidity=time_validity,
    )
    return registry.get_client(account).place_stop_order(stop_request)


@mcp.tool("place_stop_limit_order")
def place_stop_limit_order(
    ticker: str,
    quantity: float,
    stop_price: float,
    limit_price: float,
    account: str,
    time_validity: StopLimitRequestTimeValidityEnum = StopLimitRequestTimeValidityEnum.DAY,
) -> Order:
    """
    Place a stop-limit order to buy or sell an instrument when the market
    price reaches a specified stop price, then execute at a specified limit
    price or better.

    Args:
        ticker: Ticker symbol of the instrument to trade (e.g., 'AAPL_US_EQ')
        quantity: Number of shares/units to trade
        stop_price: Stop price that triggers the limit order
        limit_price: Limit price for the order
        account: Account name to place the order in (required)
        time_validity: Time validity of the order. Defaults to DAY.
            Possible values: DAY, GOOD_TILL_CANCEL

    Returns:
        Order: Details of the placed order
    """
    stop_limit_request = StopLimitRequest(
        ticker=ticker,
        quantity=quantity,
        stopPrice=stop_price,
        limitPrice=limit_price,
        timeValidity=time_validity,
    )
    return registry.get_client(account).place_stop_limit_order(stop_limit_request)


@mcp.tool("cancel_order")
def cancel_order_by_id(order_id: int, account: str) -> None:
    """
    Cancel an existing order.

    Args:
        order_id: ID of the order to cancel
        account: Account name that owns the order (required)
    """
    return registry.get_client(account).cancel_order(order_id)


@mcp.tool("fetch_order")
def fetch_order_by_id(order_id: int, account: Union[str, list[str], None] = None):
    """
    Fetch a specific order by ID.

    Args:
        order_id: ID of the order to fetch
        account: Account name, list of names, "all", or None for default account.
    """
    clients = registry.resolve(account)
    results = {}
    for name, c in clients.items():
        try:
            results[name] = c.get_order_by_id(order_id)
        except Exception as e:
            results[name] = e
    return format_response(results)


# Account Data
@mcp.tool("fetch_account_info")
def fetch_account_info(account: Union[str, list[str], None] = None):
    """
    Fetch account metadata.

    Args:
        account: Account name, list of names, "all", or None for default account.
    """
    clients = registry.resolve(account)
    results = {}
    for name, c in clients.items():
        try:
            results[name] = c.get_account_info()
        except Exception as e:
            results[name] = e
    return format_response(results)


@mcp.tool("fetch_account_cash")
def fetch_account_cash(account: Union[str, list[str], None] = None):
    """
    Fetch account cash balance.

    Args:
        account: Account name, list of names, "all", or None for default account.
        When querying multiple accounts, numeric fields are summed in a __totals__ entry.
    """
    clients = registry.resolve(account)
    results = {}
    for name, c in clients.items():
        try:
            results[name] = c.get_account_cash()
        except Exception as e:
            results[name] = e
    return format_response(results, compute_totals=True)


# Personal Portfolio
@mcp.tool("fetch_all_open_positions")
def fetch_all_open_positions(account: Union[str, list[str], None] = None):
    """
    Fetch all open positions.

    Args:
        account: Account name, list of names, "all", or None for default account.
    """
    clients = registry.resolve(account)
    results = {}
    for name, c in clients.items():
        try:
            results[name] = c.get_account_positions()
        except Exception as e:
            results[name] = e
    return format_response(results)


@mcp.tool("fetch_open_position_by_ticker")
def fetch_open_position_by_ticker(ticker: str, account: Union[str, list[str], None] = None):
    """
    Fetch a position by ticker (deprecated).

    Args:
        ticker: Ticker symbol to look up
        account: Account name, list of names, "all", or None for default account.
    """
    clients = registry.resolve(account)
    results = {}
    for name, c in clients.items():
        try:
            results[name] = c.get_account_position_by_ticker(ticker)
        except Exception as e:
            results[name] = e
    return format_response(results)


@mcp.tool("search_specific_position_by_ticker")
def search_position_by_ticker(ticker: str, account: Union[str, list[str], None] = None):
    """
    Search for a position by ticker using POST endpoint.

    Args:
        ticker: Ticker symbol to search for
        account: Account name, list of names, "all", or None for default account.
    """
    clients = registry.resolve(account)
    results = {}
    for name, c in clients.items():
        try:
            results[name] = c.search_position_by_ticker(ticker)
        except Exception as e:
            results[name] = e
    return format_response(results)


# Historical items
@mcp.tool("fetch_historical_order_data")
def fetch_historical_order_data(
    cursor: int = None,
    ticker: str = None,
    limit: int = 20,
    account: Union[str, list[str], None] = None,
):
    """
    Fetch historical order data with pagination.

    Args:
        cursor: Pagination cursor
        ticker: Filter by ticker symbol
        limit: Max results (default 20)
        account: Account name, list of names, "all", or None for default account.
    """
    clients = registry.resolve(account)
    results = {}
    for name, c in clients.items():
        try:
            results[name] = c.get_historical_order_data(cursor=cursor, ticker=ticker, limit=limit)
        except Exception as e:
            results[name] = e
    return format_response(results)


@mcp.tool("fetch_paid_out_dividends")
def fetch_paid_out_dividends(
    cursor: int = None,
    ticker: str = None,
    limit: int = 20,
    account: Union[str, list[str], None] = None,
):
    """
    Fetch historical dividend data with pagination.

    Args:
        cursor: Pagination cursor
        ticker: Filter by ticker symbol
        limit: Max results (default 20)
        account: Account name, list of names, "all", or None for default account.
    """
    clients = registry.resolve(account)
    results = {}
    for name, c in clients.items():
        try:
            results[name] = c.get_dividends(cursor=cursor, ticker=ticker, limit=limit)
        except Exception as e:
            results[name] = e
    return format_response(results)


@mcp.tool("fetch_exports_list")
def fetch_exports_list(account: Union[str, list[str], None] = None):
    """
    Lists detailed information about all csv account exports.

    Args:
        account: Account name, list of names, "all", or None for default account.
    """
    clients = registry.resolve(account)
    results = {}
    for name, c in clients.items():
        try:
            results[name] = c.get_reports()
        except Exception as e:
            results[name] = e
    return format_response(results)


@mcp.tool("request_csv_export")
def request_csv_export(
    account: str,
    include_dividends: bool = True,
    include_interest: bool = True,
    include_orders: bool = True,
    include_transactions: bool = True,
    time_from: str = None,
    time_to: str = None,
) -> EnqueuedReportResponse:
    """
    Request a CSV export of the account's orders, dividends and transactions
    history.

    Args:
        account: Account name to export data for (required)
        include_dividends: Whether to include dividend information. Defaults to True
        include_interest: Whether to include interest information. Defaults to True
        include_orders: Whether to include order history. Defaults to True
        include_transactions: Whether to include transaction history. Defaults to True
        time_from: Start time in ISO 8601 format (e.g., '2023-01-01T00:00:00Z')
        time_to: End time in ISO 8601 format (e.g., '2023-12-31T23:59:59Z')

    Returns:
        EnqueuedReportResponse: Response containing the report ID and status
    """
    client = registry.get_client(account)
    data_included = ReportDataIncluded(
        includeDividends=include_dividends,
        includeInterest=include_interest,
        includeOrders=include_orders,
        includeTransactions=include_transactions,
    )
    return client.request_export(
        data_included=data_included, time_from=time_from, time_to=time_to
    )


@mcp.tool("fetch_transaction_list")
def fetch_transaction_list(
    cursor: str | None = None,
    time: str | None = None,
    limit: int = 20,
    account: Union[str, list[str], None] = None,
):
    """
    Fetch superficial information about movements to and from your account.

    Args:
        cursor: Pagination cursor
        time: Start time in ISO 8601 format
        limit: Max results (default 20)
        account: Account name, list of names, "all", or None for default account.
    """
    clients = registry.resolve(account)
    results = {}
    for name, c in clients.items():
        try:
            results[name] = c.get_history_transactions(cursor=cursor, time_from=time, limit=limit)
        except Exception as e:
            results[name] = e
    return format_response(results)
