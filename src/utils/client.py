import base64
import os
from typing import Any, Optional

import hishel
import httpx

from models import *
from utils.hishel_config import controller, storage


class Trading212Client:
    def __init__(
        self,
        api_key: str | None = None,
        api_secret: str | None = None,
        environment: str | None = None,
        version: str = "v0",
    ):
        api_key = api_key or os.getenv("TRADING212_API_KEY")
        api_secret = api_secret or os.getenv("TRADING212_API_SECRET")
        environment = environment or os.getenv("ENVIRONMENT") or Environment.DEMO.value

        if not api_key:
            raise ValueError("TRADING212_API_KEY must be configured")

        base_url = f"https://{environment}.trading212.com/api/{version}"
        headers = self._build_headers(api_key=api_key, api_secret=api_secret)

        self.client = hishel.CacheClient(
            base_url=base_url,
            storage=storage,
            controller=controller,
            headers=headers,
        )

    @staticmethod
    def _build_headers(api_key: str, api_secret: str | None) -> dict[str, str]:
        # The current public API prefers HTTP Basic auth using API key + secret,
        # but the spec still exposes a legacy API-key-only header for compatibility.
        if api_secret:
            token = base64.b64encode(f"{api_key}:{api_secret}".encode("utf-8")).decode(
                "utf-8"
            )
            authorization = f"Basic {token}"
        else:
            authorization = api_key

        return {
            "Authorization": authorization,
            "Content-Type": "application/json",
        }

    @staticmethod
    def _normalise_path(path: str) -> str:
        if path.startswith("/api/"):
            _, _, rest = path.partition("/api/v0")
            return rest or "/"
        return path

    def _make_request(self, method: str, url: str, **kwargs) -> Any:
        response = self.client.request(method, self._normalise_path(url), **kwargs)

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            detail = None
            try:
                detail = response.json()
            except ValueError:
                detail = response.text

            raise RuntimeError(
                f"Trading 212 API request failed ({response.status_code}) for "
                f"{method} {response.request.url.path}: {detail}"
            ) from exc

        if response.status_code == 204 or not response.content:
            return None

        return response.json()

    def get_account_summary(self) -> AccountSummary:
        """Fetch the account summary."""
        data = self._make_request("GET", "/equity/account/summary")
        return AccountSummary.model_validate(data)

    def get_account_cash(self) -> Cash:
        """Fetch account cash from the account summary endpoint."""
        account_summary = self.get_account_summary()
        return Cash.model_validate(account_summary.cash.model_dump() if account_summary.cash else {})

    def get_account_positions(self) -> list[Position]:
        """Fetch all open positions."""
        data = self._make_request("GET", "/equity/positions")
        return [Position.model_validate(position) for position in data]

    def get_positions(self, ticker: str | None = None) -> list[Position]:
        """Fetch positions, optionally filtered by ticker."""
        params = {"ticker": ticker} if ticker else None
        data = self._make_request("GET", "/equity/positions", params=params)
        return [Position.model_validate(position) for position in data]

    def get_position_by_ticker(self, ticker: str) -> Position:
        """Fetch a single open position by ticker via the current filter API."""
        positions = self.get_positions(ticker=ticker)
        if not positions:
            raise RuntimeError(f"No open position found for ticker '{ticker}'")
        return positions[0]

    def get_account_position_by_ticker(self, ticker: str) -> Position:
        """Deprecated alias for fetching a single position by ticker."""
        return self.get_position_by_ticker(ticker)

    def search_position_by_ticker(self, ticker: str) -> Position:
        """Deprecated alias for fetching a single position by ticker."""
        return self.get_position_by_ticker(ticker)

    def get_dividends(
        self,
        cursor: Optional[int] = None,
        ticker: Optional[str] = None,
        limit: int = 20,
    ) -> PaginatedResponseHistoryDividendItem:
        """Fetch dividend history with optional pagination."""
        params = {}
        if cursor is not None:
            params["cursor"] = cursor
        if ticker is not None:
            params["ticker"] = ticker
        params["limit"] = min(50, max(1, limit))

        data = self._make_request("GET", "/equity/history/dividends", params=params)
        return PaginatedResponseHistoryDividendItem.model_validate(data)

    def get_orders(self) -> list[Order]:
        """Fetch current orders."""
        data = self._make_request("GET", "/equity/orders")
        return [Order.model_validate(order) for order in data]

    def get_order_by_id(self, order_id: int) -> Order:
        """Fetch a specific order by ID."""
        data = self._make_request("GET", f"/equity/orders/{order_id}")
        return Order.model_validate(data)

    def get_pies(self) -> list[AccountBucketResultResponse]:
        """Fetch all pies."""
        data = self._make_request("GET", "/equity/pies")
        return [AccountBucketResultResponse.model_validate(pie) for pie in data]

    def get_pie_by_id(self, pie_id: int) -> AccountBucketInstrumentsDetailedResponse:
        """Fetch a specific pie by ID."""
        data = self._make_request("GET", f"/equity/pies/{pie_id}")
        return AccountBucketInstrumentsDetailedResponse.model_validate(data)

    def create_pie(self, pie_data: PieRequest) -> AccountBucketInstrumentsDetailedResponse:
        """Create a new pie."""
        data = self._make_request(
            "POST",
            "/equity/pies",
            json=pie_data.model_dump(mode="json", exclude_none=True),
        )
        return AccountBucketInstrumentsDetailedResponse.model_validate(data)

    def update_pie(self, pie_id: int, pie_data: PieRequest) -> AccountBucketInstrumentsDetailedResponse:
        """Update a specific pie by ID."""
        data = self._make_request(
            "POST",
            f"/equity/pies/{pie_id}",
            json=pie_data.model_dump(mode="json", exclude_none=True),
        )
        return AccountBucketInstrumentsDetailedResponse.model_validate(data)

    def duplicate_pie(
        self,
        pie_id: int,
        duplicate_bucket_request: DuplicateBucketRequest,
    ) -> AccountBucketInstrumentsDetailedResponse:
        """Duplicate a pie."""
        data = self._make_request(
            "POST",
            f"/equity/pies/{pie_id}/duplicate",
            json=duplicate_bucket_request.model_dump(mode="json", exclude_none=True),
        )
        return AccountBucketInstrumentsDetailedResponse.model_validate(data)

    def delete_pie(self, pie_id: int) -> None:
        """Delete a pie."""
        self._make_request("DELETE", f"/equity/pies/{pie_id}")

    def get_historical_order_data(
        self,
        cursor: Optional[int] = None,
        ticker: Optional[str] = None,
        limit: int = 20,
    ) -> PaginatedResponseHistoricalOrder:
        """Fetch historical order data with pagination."""
        params = {"limit": min(50, max(1, limit))}
        if cursor is not None:
            params["cursor"] = cursor
        if ticker is not None:
            params["ticker"] = ticker

        data = self._make_request("GET", "/equity/history/orders", params=params)
        return PaginatedResponseHistoricalOrder.model_validate(data)

    def get_history_transactions(
        self,
        cursor: Optional[str] = None,
        time_from: Optional[str] = None,
        limit: int = 20,
    ) -> PaginatedResponseHistoryTransactionItem:
        """Fetch movements to and from the account."""
        params = {"limit": min(50, max(1, limit))}
        if cursor is not None:
            params["cursor"] = cursor
        if time_from is not None:
            params["time"] = time_from

        data = self._make_request("GET", "/equity/history/transactions", params=params)
        return PaginatedResponseHistoryTransactionItem.model_validate(data)

    def get_instruments(self) -> list[TradeableInstrument]:
        """Fetch all tradeable instruments."""
        data = self._make_request("GET", "/equity/metadata/instruments")
        return [TradeableInstrument.model_validate(instrument) for instrument in data]

    def get_exchanges(self) -> list[Exchange]:
        """Fetch all exchanges and their working schedules."""
        data = self._make_request("GET", "/equity/metadata/exchanges")
        return [Exchange.model_validate(exchange) for exchange in data]

    def place_market_order(self, order_data: MarketRequest) -> Order:
        """Place a market order."""
        data = self._make_request(
            "POST",
            "/equity/orders/market",
            json=order_data.model_dump(mode="json", exclude_none=True),
        )
        return Order.model_validate(data)

    def place_limit_order(self, order_data: LimitRequest) -> Order:
        """Place a limit order."""
        data = self._make_request(
            "POST",
            "/equity/orders/limit",
            json=order_data.model_dump(mode="json", exclude_none=True),
        )
        return Order.model_validate(data)

    def place_stop_order(self, order_data: StopRequest) -> Order:
        """Place a stop order."""
        data = self._make_request(
            "POST",
            "/equity/orders/stop",
            json=order_data.model_dump(mode="json", exclude_none=True),
        )
        return Order.model_validate(data)

    def place_stop_limit_order(self, order_data: StopLimitRequest) -> Order:
        """Place a stop-limit order."""
        data = self._make_request(
            "POST",
            "/equity/orders/stop_limit",
            json=order_data.model_dump(mode="json", exclude_none=True),
        )
        return Order.model_validate(data)

    def cancel_order(self, order_id: int) -> None:
        """Cancel an existing order."""
        self._make_request("DELETE", f"/equity/orders/{order_id}")

    def get_reports(self) -> list[ReportResponse]:
        """Get account export reports."""
        data = self._make_request("GET", "/equity/history/exports")
        return [ReportResponse.model_validate(report) for report in data]

    def request_export(
        self,
        data_included: ReportDataIncluded | None = None,
        time_from: str | None = None,
        time_to: str | None = None,
    ) -> EnqueuedReportResponse:
        """Request a CSV export of the account history."""
        data_included = data_included or ReportDataIncluded()
        payload: dict[str, Any] = {
            "dataIncluded": data_included.model_dump(mode="json", exclude_none=True),
        }
        if time_from:
            payload["timeFrom"] = time_from
        if time_to:
            payload["timeTo"] = time_to

        data = self._make_request("POST", "/equity/history/exports", json=payload)
        return EnqueuedReportResponse.model_validate(data)
