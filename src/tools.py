from typing import Optional
from mcp_server import mcp, client

from models import *


### Instruments Metadata
@mcp.tool("search_instrument")
def search_instrument(search_term: str = None) -> list[TradeableInstrument]:
    """
    Fetch instruments, optionally filtered by ticker or name.
    
    Args:
        search_term: Search term to filter instruments by ticker or name (case-insensitive)
        
    Returns:
        List of matching TradeableInstrument objects, or all instruments if no search term is provided
    """
    instruments = client.get_instruments()
    
    if not search_term:
        return instruments
        
    search_lower = search_term.lower()
    return [
        inst for inst in instruments
        if (inst.ticker and search_lower in inst.ticker.lower()) or 
           (inst.name and search_lower in inst.name.lower())
    ]


@mcp.tool("search_exchange")
def search_exchange(search_term: str = None) -> list[Exchange]:
    """
    Fetch exchanges, optionally filtered by name or ID.
    
    Args:
        search_term: Optional search term to filter exchanges by name or ID (case-insensitive)
        
    Returns:
        List of matching Exchange objects, or all exchanges if no search term is provided
    """
    exchanges = client.get_exchanges()
    
    if not search_term:
        return exchanges
        
    search_lower = search_term.lower()
    return [
        exch for exch in exchanges
        if (exch.name and search_lower in exch.name.lower()) or 
           (str(exch.id) == search_term)
    ]


### Pies
@mcp.tool("fetch_pies")
def fetch_pies() -> list[AccountBucketResultResponse]:
    """Fetch all pies."""
    return client.get_pies()

@mcp.tool("create_pie")
def create_pie(
    name: str = Field(
        ...,
        description="Name of the pie"
    ),
    instrument_shares: dict[str, float] = Field(
        ...,
        description="Dictionary mapping instrument tickers to their weights in the pie (e.g., {'AAPL_US_EQ': 0.5, 'MSFT_US_EQ': 0.5})",
        example={"AAPL_US_EQ": 0.5, "MSFT_US_EQ": 0.5}
    ),
    dividend_cash_action: Optional[DividendCashActionEnum] = Field(
        default=DividendCashActionEnum.REINVEST,
        description="How dividends are handled",
        examples=[DividendCashActionEnum.REINVEST, DividendCashActionEnum.TO_ACCOUNT_CASH]
    ),
    end_date: Optional[datetime] = Field(
        default=None,
        description="Optional end date for the pie in ISO 8601 format (e.g., '2024-12-31T23:59:59Z')"
    ),
    goal: Optional[float] = Field(
        default=None,
        description="Total desired value of the pie in account currency"
    ),
    icon: Optional[str] = Field(
        default=None,
        description="Optional icon identifier for the pie"
    )
) -> AccountBucketInstrumentsDetailedResponse:
    """
    Create a new pie with the specified parameters.
    
    Returns:
        AccountBucketInstrumentsDetailedResponse: Details of the created pie
    """
    pie_data = PieRequest(
        name=name,
        instrumentShares=instrument_shares,
        dividendCashAction=dividend_cash_action,
        endDate=end_date,
        goal=goal,
        icon=icon
    )
    return client.create_pie(pie_data)

@mcp.tool("delete_pie")
def delete_pie(pie_id: int) -> None:
    """Delete a pie."""
    client.delete_pie(pie_id)
    
@mcp.tool("fetch_a_pie")
def fetch_a_pie(pie_id: int) -> AccountBucketResultResponse:
    """Fetch a specific pie by ID."""
    return client.get_pie_by_id(pie_id)

@mcp.tool("update_pie")
def update_pie(
    pie_id: int,
    name: str = Field(
        default=None,
        description="New name for the pie"
    ),
    instrument_shares: dict[str, float] = Field(
        default=None,
        description="Dictionary mapping instrument tickers to their new weights in the pie (e.g., {'AAPL_US_EQ': 0.5, 'MSFT_US_EQ': 0.5})",
        examples=[{"AAPL_US_EQ": 0.5, "MSFT_US_EQ": 0.5}]
    ),
    dividend_cash_action: Optional[DividendCashActionEnum] = Field(
        default=None,
        description="How dividends should be handled",
        examples=[DividendCashActionEnum.REINVEST, DividendCashActionEnum.TO_ACCOUNT_CASH]
    ),
    end_date: Optional[datetime] = Field(
        default=None,
        description="New end date for the pie in ISO 8601 format (e.g., '2024-12-31T23:59:59Z')"
    ),
    goal: Optional[float] = Field(
        default=None,
        description="New total desired value of the pie in account currency"
    ),
    icon: Optional[str] = Field(
        default=None,
        description="New icon identifier for the pie"
    )
) -> AccountBucketInstrumentsDetailedResponse:
    """
    Update an existing pie with new parameters. The pie must be renamed when updating it.
    
    Returns:
        AccountBucketInstrumentsDetailedResponse: Updated details of the pie
    """
    pie_data = PieRequest(
        name=name,
        instrumentShares=instrument_shares,
        dividendCashAction=dividend_cash_action,
        endDate=end_date,
        goal=goal,
        icon=icon
    )
    return client.update_pie(pie_id, pie_data)

@mcp.tool("duplicate_pie")
def duplicate_pie(
    pie_id: int,
    name: Optional[str] = Field(
        default=None,
        description="Optional new name for the duplicated pie. If not provided, will use original name with copy suffix."
    ),
    icon: Optional[str] = Field(
        default=None,
        description="Optional new icon identifier for the duplicated pie"
    )
) -> AccountBucketResultResponse:
    """
    Create a duplicate of an existing pie.
    
    Args:
        pie_id: ID of the pie to duplicate
        name: Optional new name for the duplicated pie
        icon: Optional new icon for the duplicated pie
        
    Returns:
        AccountBucketResultResponse: Details of the duplicated pie
    """
    duplicate_request = DuplicateBucketRequest(
        name=name,
        icon=icon
    )
    return client.duplicate_pie(pie_id, duplicate_request)


### Equity Orders
@mcp.tool("fetch_all_orders")
def fetch_orders() -> list[Order]:
    """Fetch all equity orders."""
    return client.get_orders()

@mcp.tool("place_limit_order")
def place_limit_order(
    ticker: str = Field(
        ...,
        description="Ticker symbol of the instrument to trade (e.g., 'AAPL_US_EQ')"
    ),
    quantity: float = Field(
        ...,
        description="Number of shares/units to trade"
    ),
    limit_price: float = Field(
        ...,
        description="Limit price for the order"
    ),
    time_validity: LimitRequestTimeValidityEnum = Field(
        default=LimitRequestTimeValidityEnum.DAY,
        description="Time validity of the order",
        examples=[LimitRequestTimeValidityEnum.DAY, LimitRequestTimeValidityEnum.GOOD_TILL_CANCEL]
    )
) -> Order:
    """
    Place a limit order to buy or sell an instrument at a specified price or better.
    
    Returns:
        Order: Details of the placed order
    """
    limit_request = LimitRequest(
        ticker=ticker,
        quantity=quantity,
        limitPrice=limit_price,
        timeValidity=time_validity
    )
    return client.place_limit_order(limit_request)

@mcp.tool("place_market_order")
def place_market_order(
    ticker: str = Field(
        ...,
        description="Ticker symbol of the instrument to trade (e.g., 'AAPL_US_EQ')"
    ),
    quantity: float = Field(
        ...,
        description="Number of shares/units to trade"
    )
) -> Order:
    """
    Place a market order to buy or sell an instrument at the current market price.
    
    Returns:
        Order: Details of the placed order
    """
    market_request = MarketRequest(
        ticker=ticker,
        quantity=quantity
    )
    return client.place_market_order(market_request)

@mcp.tool("place_stop_order")
def place_stop_order(
    ticker: str = Field(
        ...,
        description="Ticker symbol of the instrument to trade (e.g., 'AAPL_US_EQ')"
    ),
    quantity: float = Field(
        ...,
        description="Number of shares/units to trade"
    ),
    stop_price: float = Field(
        ...,
        description="Stop price that triggers the order"
    ),
    time_validity: StopRequestTimeValidityEnum = Field(
        default=StopRequestTimeValidityEnum.DAY,
        description="Time validity of the order",
        examples=[StopRequestTimeValidityEnum.DAY, StopRequestTimeValidityEnum.GOOD_TILL_CANCEL]
    )
) -> Order:
    """
    Place a stop order to buy or sell an instrument when the market price reaches a specified stop price.
    
    Returns:
        Order: Details of the placed order
    """
    stop_request = StopRequest(
        ticker=ticker,
        quantity=quantity,
        stopPrice=stop_price,
        timeValidity=time_validity
    )
    return client.place_stop_order(stop_request)


@mcp.tool("place_stop_limit_order")
def place_stop_limit_order(
    ticker: str = Field(
        ...,
        description="Ticker symbol of the instrument to trade (e.g., 'AAPL_US_EQ')"
    ),
    quantity: float = Field(
        ...,
        description="Number of shares/units to trade"
    ),
    stop_price: float = Field(
        ...,
        description="Stop price that triggers the limit order"
    ),
    limit_price: float = Field(
        ...,
        description="Limit price for the order"
    ),
    time_validity: StopLimitRequestTimeValidityEnum = Field(
        default=StopLimitRequestTimeValidityEnum.DAY,
        description="Time validity of the order",
        examples=[StopLimitRequestTimeValidityEnum.DAY, StopLimitRequestTimeValidityEnum.GOOD_TILL_CANCEL]
    )
) -> Order:
    """
    Place a stop-limit order to buy or sell an instrument when the market price reaches a specified stop price,
    then execute at a specified limit price or better.
    
    Returns:
        Order: Details of the placed order
    """
    stop_limit_request = StopLimitRequest(
        ticker=ticker,
        quantity=quantity,
        stopPrice=stop_price,
        limitPrice=limit_price,
        timeValidity=time_validity
    )
    return client.place_stop_limit_order(stop_limit_request)

@mcp.tool("cancel_order")
def cancel_order_by_id(order_id: int) -> None:
    """Cancel an existing order."""
    return client.cancel_order(order_id)


@mcp.tool("fetch_order")
def fetch_order_by_id(order_id: int) -> Order:
    """Fetch a specific order by ID."""
    return client.get_order_by_id(order_id)

### Account Data
@mcp.tool("fetch_account_info")
def fetch_account_info() -> Account:
    """Fetch account metadata."""
    return client.get_account_info()

@mcp.tool("fetch_account_cash")
def fetch_account_cash() -> Cash:
    """Fetch account cash balance."""
    return client.get_account_cash()


### Personal Portfolio
@mcp.tool("fetch_all_open_positions")
def fetch_all_open_positions() -> list[Position]:
    """Fetch all open positions."""
    return client.get_account_positions()

@mcp.tool("fetch_open_position_by_ticker")
def fetch_open_position_by_ticker(ticker: str) -> Position:
    """Fetch a position by ticker (deprecated)."""
    return client.get_account_position_by_ticker(ticker)

@mcp.tool("search_specific_position_by_ticker")
def search_position_by_ticker(ticker: str) -> Position:
    """Search for a position by ticker using POST endpoint."""
    return client.search_position_by_ticker(ticker)


### Historical items
@mcp.tool("fetch_historical_order_data")
def fetch_historical_order_data(cursor: int = None, ticker: str = None,
                       limit: int = 20) -> list[HistoricalOrder]:
    """Fetch historical order data with pagination."""
    return client.get_historical_order_data(cursor=cursor, ticker=ticker, limit=limit)

@mcp.tool("fetch_paid_out_dividends")
def fetch_paid_out_dividends(cursor: int = None, ticker: str = None,
                  limit: int = 20) -> PaginatedResponseHistoryDividendItem:
    """Fetch historical dividend data with pagination."""
    return client.get_dividends(cursor=cursor, ticker=ticker, limit=limit)

@mcp.tool("fetch_exports_list")
def fetch_exports_list() -> list[ReportResponse]:
    """Lists detailed information about all csv account exports."""
    return client.get_reports()

@mcp.tool("request_csv_export")
def request_csv_export(
    include_dividends: bool = Field(
        default=True,
        description="Whether to include dividend information in the export"
    ),
    include_interest: bool = Field(
        default=True,
        description="Whether to include interest information in the export"
    ),
    include_orders: bool = Field(
        default=True,
        description="Whether to include order history in the export"
    ),
    include_transactions: bool = Field(
        default=True,
        description="Whether to include transaction history in the export"
    ),
    time_from: str = Field(
        default=None,
        description="Start time for the report in ISO 8601 format (e.g., '2023-01-01T00:00:00Z')"
    ),
    time_to: str = Field(
        default=None,
        description="End time for the report in ISO 8601 format (e.g., '2023-12-31T23:59:59Z')"
    )
) -> EnqueuedReportResponse:
    """
    Request a CSV export of the account's orders, dividends and transactions history.
    Once the export is complete it can be accessed from the download link in the exports list.
    
    Returns:
        EnqueuedReportResponse: Response containing the report ID and status
    """
    data_included = ReportDataIncluded(
        includeDividends=include_dividends,
        includeInterest=include_interest,
        includeOrders=include_orders,
        includeTransactions=include_transactions
    )
    return client.request_export(data_included=data_included, time_from=time_from, time_to=time_to)

@mcp.tool("fetch_transaction_list")
def fetch_transaction_list(cursor: str | None = None, time: str | None = None,
                  limit: int = 20) -> PaginatedResponseHistoryTransactionItem:
    """Fetch superficial information about movements to and from your account."""
    return client.get_history_transactions(cursor=cursor, time=time, limit=limit)
