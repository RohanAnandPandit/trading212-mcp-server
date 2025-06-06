import httpx
import os
import hishel
from typing import Optional, List, Any

from models import *

from utils.hishel_config import storage, controller


class Trading212Client:
    def __init__(self, api_key: str = None, environment: str = None,
                 version: str = "v0"):
        api_key = api_key or os.getenv("TRADING212_API_KEY")
        environment = environment or os.getenv("ENVIRONMENT") or Environment.DEMO.value
        base_url = f"https://{environment}.trading212.com/api/{version}"
        headers = {"Authorization": api_key, "Content-Type": "application/json"}
        self.client = hishel.CacheClient(base_url=base_url, storage=storage,
                                         controller=controller, headers=headers)

    def _make_requests(self, method: str, url: str, **kwargs) -> Any:
        try:
            response = self.client.request(method, url, **kwargs)               
            return response.json()
        except httpx.HTTPStatusError as e:
            print(f"HTTP error occurred: {e}")
            raise Exception(f"HTTP error occurred: {e}")

    def get_account_info(self) -> Account:
        """Fetch account metadata"""
        data = self._make_requests("GET", "/equity/account/info")
        return Account.model_validate(data)

    def get_account_cash(self) -> Cash:
        """Fetch account cash"""
        data = self._make_requests("GET", "/equity/account/cash")
        return Cash.model_validate(data)

    def get_account_positions(self) -> List[Position]:
        """Fetch all open positions"""
        data = self._make_requests("GET", "/equity/portfolio")
        return [Position.model_validate(pos) for pos in data]

    def get_account_position_by_ticker(self, ticker: str) -> Position:
        """Fetch an open position by ticker"""
        data = self._make_requests("GET", f"/equity/portfolio/{ticker}")
        return Position.model_validate(data)

    def search_position_by_ticker(self, ticker: str) -> Position:
        """Search for an open position by ticker using POST"""
        data = self._make_requests("POST", f"/equity/portfolio/ticker",
                                   json={"ticker": ticker})
        return Position.model_validate(data)
    
    def get_dividends(self, 
                      cursor: Optional[int] = None, 
                      ticker: Optional[str] = None, 
                      limit: int = 20) -> PaginatedResponseHistoryDividendItem:
        """
        Fetch dividend history with optional pagination, ticker filtering, and limit.

        Args:
            cursor: Pagination cursor for the next page of results
            ticker: Filter dividends by ticker symbol
            limit: Maximum number of items to return (max: 50, default: 20)

        Returns:
            PaginatedResponseHistoryDividendItem: Paginated response containing dividend items
        """
        params = {}
        if cursor is not None:
            params["cursor"] = cursor
        if ticker is not None:
            params["ticker"] = ticker
        if limit is not None:
            params["limit"] = min(50, max(1, limit))  # Ensure limit is between 1 and 50

        data = self._make_requests("GET", "/history/dividends", params=params)
        return PaginatedResponseHistoryDividendItem.model_validate(data)

    def get_orders(self) -> List[Order]:
        """Fetch current orders."""
        data = self._make_requests("GET", f"/equity/orders")
        return [Order.model_validate(order) for order in data]

    def get_order_by_id(self, order_id: int) -> Order:
        """Fetch a specific order by ID."""
        data = self._make_requests("GET", f"/equity/orders/{order_id}")
        return Order.model_validate(data)

    def get_pies(self) -> List[AccountBucketResultResponse]:
        """Fetch all pies."""
        data = self._make_requests("GET", f"/equity/pies")
        return [AccountBucketResultResponse.model_validate(pie) for pie in data]

    def get_pie_by_id(self, pie_id: int) -> AccountBucketInstrumentsDetailedResponse:
        """Fetch a specific pie by ID."""
        data = self._make_requests("GET", f"/equity/pies/{pie_id}")
        return AccountBucketInstrumentsDetailedResponse.model_validate(data)
    
    def create_pie(self, pie_data: PieRequest) -> AccountBucketInstrumentsDetailedResponse:
        """Create a new pie."""
        data = self._make_requests("POST", f"/equity/pies", json=pie_data.model_dump(mode="json"))
        return AccountBucketInstrumentsDetailedResponse.model_validate(data)
    
    def update_pie(self, pie_id: int, pie_data: PieRequest) -> AccountBucketInstrumentsDetailedResponse:
        """Update a specific pie by ID."""
        pie_data = pie_data.model_dump(mode="json")
        pie_data = {k: v for k, v in pie_data.items() if v is not None}
        data = self._make_requests("POST", f"/equity/pies/{pie_id}", json=pie_data)
        return AccountBucketInstrumentsDetailedResponse.model_validate(data)

    def duplicate_pie(self, pie_id: int, duplicate_bucket_request: DuplicateBucketRequest) -> AccountBucketInstrumentsDetailedResponse:
        """Duplicate a pie."""
        data = self._make_requests("POST", f"/equity/pies/{pie_id}/duplicate", json=duplicate_bucket_request.model_dump(mode="json"))
        return AccountBucketInstrumentsDetailedResponse.model_validate(data)

    def delete_pie(self, pie_id: int):
        """Delete a pie."""
        return self._make_requests("DELETE", f"/equity/pies/{pie_id}")

    def get_historical_order_data(self, cursor: Optional[int] = None,
                           ticker: Optional[str] = None, limit: int = 20) -> \
            List[HistoricalOrder]:
        """Fetch historical order data with pagination"""
        params = {"limit": limit}
        if cursor is not None:
            params["cursor"] = cursor
        if ticker is not None:
            params["ticker"] = ticker

        data = self._make_requests("GET", f"/equity/history/orders",
                                   params=params)
        return [HistoricalOrder.model_validate(order) for order in
                data["items"]]

    def get_history_dividends(self, cursor: Optional[int] = None,
                              ticker: Optional[str] = None,
                              limit: int = 20) -> PaginatedResponseHistoryDividendItem:
        """Fetch historical dividend data with pagination"""
        params = {"limit": limit}
        if cursor is not None:
            params["cursor"] = cursor
        if ticker is not None:
            params["ticker"] = ticker

        data = self._make_requests("GET", f"/equity/history/dividends",
                                   params=params)
        return PaginatedResponseHistoryDividendItem.model_validate(data)

    def get_history_transactions(self, cursor: Optional[str] = None,
                                 time_from: Optional[str] = None,
                                 limit: int = 20) -> PaginatedResponseHistoryTransactionItem:
        """
        Fetch superficial information about movements to and from your account
        
        Args:
            cursor: Pagination cursor for the next page of results
            time: Retrieve transactions starting from the specified time (ISO 8601 format)
            limit: Maximum number of items to return (max: 50, default: 20)
            
        Returns:
            PaginatedResponseHistoryTransactionItem: Paginated response containing transaction items
        """        
        params = {"limit": limit}
        if cursor is not None:
            params["cursor"] = cursor
        if time_from is not None:
            params["time"] = time_from

        data = self._make_requests("GET", f"/equity/history/transactions",
                                   params=params)
        return PaginatedResponseHistoryTransactionItem.model_validate(data)

    def get_instruments(self) -> List[TradeableInstrument]:
        """Fetch all tradeable instruments"""
        data = self._make_requests("GET", f"/equity/metadata/instruments")
        return [TradeableInstrument.model_validate(instrument) for instrument in
                data]

    def get_exchanges(self) -> List[Exchange]:
        """Fetch all exchanges and their working schedules"""
        data = self._make_requests("GET", f"/equity/metadata/exchanges")
        return [Exchange.model_validate(exchange) for exchange in data]

    def place_market_order(self, order_data: MarketRequest) -> Order:
        """Place a market order"""
        data = self._make_requests("POST", f"/equity/orders/market",
                                   json=order_data.model_dump(mode="json"))
        return Order.model_validate(data)

    def place_limit_order(self, order_data: LimitRequest) -> Order:
        """Place a limit order"""
        data = self._make_requests("POST", f"/equity/orders/limit",
                                   json=order_data.model_dump(mode="json"))
        return Order.model_validate(data)
    
    def place_stop_order(self, order_data: StopRequest) -> Order:
        """Place a stop order"""
        data = self._make_requests("POST", f"/equity/orders/stop",
                                   json=order_data.model_dump(mode="json"))
        return Order.model_validate(data)

    def place_stop_limit_order(self, order_data: StopLimitRequest) -> Order:
        """Place a stop-limit order"""
        data = self._make_requests("POST", f"/equity/orders/stop_limit",
                                   json=order_data.model_dump(mode="json"))
        return Order.model_validate(data)

    def cancel_order(self, order_id: int) -> None:
        """Cancel an existing order"""
        self._make_requests("DELETE", f"/equity/orders/{order_id}")

    def get_reports(self) -> list[ReportResponse]:
        """Get account export reports"""
        data = self._make_requests("GET", f"/history/exports")
        return [ReportResponse.model_validate(report) for report in data]
        
    def request_export(self, 
                       data_included: ReportDataIncluded | None = None, 
                       time_from: str = None, 
                       time_to: str = None) -> EnqueuedReportResponse:
        """
        Request a CSV export of the account's orders, dividends and transactions history
        
        Args:
            data_included: Dictionary specifying which data to include in the report. Includes all by default.
            time_from: Start time for the report in ISO 8601 format (e.g., "2023-01-01T00:00:00Z")
            time_to: End time for the report in ISO 8601 format (e.g., "2023-12-31T23:59:59Z")
            
        Returns:
            dict: Response containing the report ID
        """
        payload = {}
        data_included = data_included or ReportDataIncluded()
        payload["dataIncluded"] = data_included.model_dump(mode="json") 
        if time_from:
            payload["timeFrom"] = time_from
        if time_to:
            payload["timeTo"] = time_to
            
        data = self._make_requests("POST", "/history/exports", json=payload)
        return EnqueuedReportResponse.model_validate(data)


if __name__ == '__main__':
    from dotenv import load_dotenv, find_dotenv

    load_dotenv(find_dotenv())

    client = Trading212Client()
    print(client.get_account_info())
