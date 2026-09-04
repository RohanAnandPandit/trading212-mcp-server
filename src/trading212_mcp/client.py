"""Trading 212 API client: one validated HTTP boundary for all endpoints."""

import base64
import json
import re
import time
from collections.abc import Callable
from email.utils import parsedate_to_datetime
from typing import Any, TypeVar
from urllib.parse import unquote, urlsplit

import httpx
from hishel import Headers, Request, Response
from pydantic import TypeAdapter, ValidationError

from .cache import ResponseCache
from .errors import (
    AuthenticationError,
    InvalidResponseError,
    RateLimitError,
    RequestError,
    UpstreamError,
)
from .models import (
    AccountBucketInstrumentsDetailedResponse,
    AccountBucketResultResponse,
    AccountSummary,
    Cash,
    DuplicateBucketRequest,
    EnqueuedReportResponse,
    Exchange,
    LimitRequest,
    MarketRequest,
    Order,
    PaginatedResponseHistoricalOrder,
    PaginatedResponseHistoryDividendItem,
    PaginatedResponseHistoryTransactionItem,
    PieRequest,
    Position,
    PublicReportRequest,
    ReportDataIncluded,
    ReportResponse,
    StopLimitRequest,
    StopRequest,
    TradeableInstrument,
)
from .settings import Settings

T = TypeVar("T")


def parse_response(schema: type[T], data: Any) -> T:
    try:
        return TypeAdapter(schema).validate_python(data)
    except ValidationError:
        raise InvalidResponseError(
            "Trading 212 returned an unexpected response format."
        ) from None


class Trading212Client:
    def __init__(
        self,
        settings: Settings,
        *,
        transport: httpx.BaseTransport | None = None,
        version: str = "v0",
        sleep: Callable[[float], None] = time.sleep,
        monotonic: Callable[[], float] = time.monotonic,
    ) -> None:
        if not re.fullmatch(r"v[0-9]+", version):
            raise ValueError("Invalid API version")
        self.base_url = f"https://{settings.environment}.trading212.com/api/{version}"
        self.version = version
        key = settings.api_key.get_secret_value()
        secret = settings.api_secret.get_secret_value() if settings.api_secret else None
        authorization = (
            ("Basic " + base64.b64encode(f"{key}:{secret}".encode()).decode())
            if secret
            else key
        )
        self.cache = ResponseCache(settings, self.base_url, authorization)
        self.http = httpx.Client(
            headers={
                "Authorization": authorization,
                "Content-Type": "application/json",
            },
            timeout=httpx.Timeout(10, connect=5),
            follow_redirects=False,
            transport=transport,
            trust_env=False,
        )
        self._sleep = sleep
        self._monotonic = monotonic

    def close(self) -> None:
        try:
            self.cache.close()
        finally:
            self.http.close()

    def __enter__(self) -> "Trading212Client":
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def _normalise_path(self, path: str) -> str:
        parsed = urlsplit(path)
        decoded = unquote(parsed.path)
        if (
            parsed.scheme
            or parsed.netloc
            or parsed.fragment
            or not path.startswith("/")
            or "\\" in decoded
            or any(part in ("..", ".") for part in decoded.split("/"))
            or any(ord(char) < 32 for char in path)
        ):
            raise RequestError("Invalid API path.")
        if parsed.path.startswith("/api/"):
            prefix = f"/api/{self.version}/"
            if not parsed.path.startswith(prefix):
                raise RequestError("API path uses a different version.")
            path = path[len(prefix) - 1 :]
        if not path.startswith("/equity/"):
            raise RequestError("Invalid API endpoint.")
        return path

    @staticmethod
    def _retry_delay(response: httpx.Response, attempt: int) -> float:
        retry_after = response.headers.get("retry-after")
        if retry_after:
            try:
                return max(0, float(retry_after))
            except ValueError:
                try:
                    return max(
                        0, parsedate_to_datetime(retry_after).timestamp() - time.time()
                    )
                except (ValueError, TypeError, OverflowError):
                    pass
        reset = response.headers.get("x-ratelimit-reset")
        if reset:
            try:
                return max(0, float(reset) - time.time())
            except ValueError:
                pass
        return float(2**attempt)

    def _send(self, request: Request, payload: Any) -> Response:
        deadline = self._monotonic() + 30
        for attempt in range(3):
            remaining = deadline - self._monotonic()
            if remaining <= 0:
                raise UpstreamError("Trading 212 request timed out.")
            try:
                # Cookies are unnecessary for API-key authentication.
                self.http.cookies.clear()
                response = self.http.request(
                    request.method,
                    request.url,
                    json=payload,
                    timeout=httpx.Timeout(
                        min(10, remaining), connect=min(5, remaining)
                    ),
                )
            except httpx.TransportError:
                if request.method != "GET" or attempt == 2:
                    raise UpstreamError(
                        "Trading 212 connection failed; a mutation's outcome may be unknown. Do not retry it automatically."
                    ) from None
                delay = float(2**attempt)
            else:
                status = response.status_code
                if status in (401, 403):
                    raise AuthenticationError(
                        "Trading 212 authentication or permission denied."
                    )
                if 200 <= status < 300:
                    body = response.content
                    if body:
                        try:
                            json.loads(body)
                        except (ValueError, UnicodeError):
                            raise InvalidResponseError(
                                "Trading 212 returned invalid JSON."
                            ) from None
                    return Response(
                        status_code=status,
                        headers=Headers(
                            {
                                "content-type": "application/json",
                                "x-trading212-retrieved-at": str(time.time()),
                            }
                        ),
                        stream=iter([body]),
                    )
                if (
                    status not in (429, 500, 502, 503, 504)
                    or request.method != "GET"
                    or attempt == 2
                ):
                    if status == 429:
                        raise RateLimitError(
                            "Trading 212 rate limit reached; retry later."
                        )
                    raise UpstreamError(f"Trading 212 request failed (HTTP {status}).")
                delay = self._retry_delay(response, attempt)
            if delay >= deadline - self._monotonic():
                raise RateLimitError(
                    "Trading 212 retry exceeds the request budget; retry later."
                )
            self._sleep(delay)
        raise UpstreamError("Trading 212 request failed.")

    def _make_request(self, method: str, url: str, **kwargs: Any) -> Any:
        path = self._normalise_path(url)
        target = httpx.URL(self.base_url + path)
        params = kwargs.get("params")
        if params:
            target = target.copy_merge_params(params)
        body = self.cache.request(
            method, str(target), lambda request: self._send(request, kwargs.get("json"))
        )
        return json.loads(body) if body else None

    def get_account_summary(self) -> AccountSummary:
        """Fetch the account summary."""
        data = self._make_request("GET", "/equity/account/summary")
        return parse_response(AccountSummary, data)

    def get_account_cash(self) -> Cash:
        """Fetch account cash from the account summary endpoint."""
        account_summary = self.get_account_summary()
        return parse_response(
            Cash, account_summary.cash.model_dump() if account_summary.cash else {}
        )

    def get_account_positions(self) -> list[Position]:
        """Fetch all open positions."""
        data = self._make_request("GET", "/equity/positions")
        return parse_response(list[Position], data)

    def get_positions(self, ticker: str | None = None) -> list[Position]:
        """Fetch positions, optionally filtered by ticker."""
        params = {"ticker": ticker} if ticker else None
        data = self._make_request("GET", "/equity/positions", params=params)
        return parse_response(list[Position], data)

    def get_position_by_ticker(self, ticker: str) -> Position:
        """Fetch a single open position by ticker via the current filter API."""
        positions = self.get_positions(ticker=ticker)
        if not positions:
            raise RequestError("No open position found for that ticker.")
        return positions[0]

    def get_account_position_by_ticker(self, ticker: str) -> Position:
        """Deprecated alias for fetching a single position by ticker."""
        return self.get_position_by_ticker(ticker)

    def search_position_by_ticker(self, ticker: str) -> Position:
        """Deprecated alias for fetching a single position by ticker."""
        return self.get_position_by_ticker(ticker)

    def get_dividends(
        self,
        cursor: int | None = None,
        ticker: str | None = None,
        limit: int = 20,
    ) -> PaginatedResponseHistoryDividendItem:
        """Fetch dividend history with optional pagination."""
        params: dict[str, int | str] = {}
        if cursor is not None:
            params["cursor"] = cursor
        if ticker is not None:
            params["ticker"] = ticker
        params["limit"] = min(50, max(1, limit))

        data = self._make_request("GET", "/equity/history/dividends", params=params)
        return parse_response(PaginatedResponseHistoryDividendItem, data)

    def get_orders(self) -> list[Order]:
        """Fetch current orders."""
        data = self._make_request("GET", "/equity/orders")
        return parse_response(list[Order], data)

    def get_order_by_id(self, order_id: int) -> Order:
        """Fetch a specific order by ID."""
        data = self._make_request("GET", f"/equity/orders/{order_id}")
        return parse_response(Order, data)

    def get_pies(self) -> list[AccountBucketResultResponse]:
        """Fetch all pies."""
        data = self._make_request("GET", "/equity/pies")
        return parse_response(list[AccountBucketResultResponse], data)

    def get_pie_by_id(self, pie_id: int) -> AccountBucketInstrumentsDetailedResponse:
        """Fetch a specific pie by ID."""
        data = self._make_request("GET", f"/equity/pies/{pie_id}")
        return parse_response(AccountBucketInstrumentsDetailedResponse, data)

    def create_pie(
        self, pie_data: PieRequest
    ) -> AccountBucketInstrumentsDetailedResponse:
        """Create a new pie."""
        data = self._make_request(
            "POST",
            "/equity/pies",
            json=pie_data.model_dump(mode="json", exclude_none=True),
        )
        return parse_response(AccountBucketInstrumentsDetailedResponse, data)

    def update_pie(
        self, pie_id: int, pie_data: PieRequest
    ) -> AccountBucketInstrumentsDetailedResponse:
        """Update a specific pie by ID."""
        if not pie_data.name or not pie_data.name.strip():
            raise RequestError("A non-empty name is required to update a pie.")
        data = self._make_request(
            "POST",
            f"/equity/pies/{pie_id}",
            json=pie_data.model_dump(mode="json", exclude_none=True),
        )
        return parse_response(AccountBucketInstrumentsDetailedResponse, data)

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
        return parse_response(AccountBucketInstrumentsDetailedResponse, data)

    def delete_pie(self, pie_id: int) -> None:
        """Delete a pie."""
        self._make_request("DELETE", f"/equity/pies/{pie_id}")

    def get_historical_order_data(
        self,
        cursor: int | None = None,
        ticker: str | None = None,
        limit: int = 20,
    ) -> PaginatedResponseHistoricalOrder:
        """Fetch historical order data with pagination."""
        params: dict[str, int | str] = {"limit": min(50, max(1, limit))}
        if cursor is not None:
            params["cursor"] = cursor
        if ticker is not None:
            params["ticker"] = ticker

        data = self._make_request("GET", "/equity/history/orders", params=params)
        return parse_response(PaginatedResponseHistoricalOrder, data)

    def get_history_transactions(
        self,
        cursor: str | None = None,
        time_from: str | None = None,
        limit: int = 20,
    ) -> PaginatedResponseHistoryTransactionItem:
        """Fetch movements to and from the account."""
        params: dict[str, int | str] = {"limit": min(50, max(1, limit))}
        if cursor is not None:
            params["cursor"] = cursor
        if time_from is not None:
            params["time"] = time_from

        data = self._make_request("GET", "/equity/history/transactions", params=params)
        return parse_response(PaginatedResponseHistoryTransactionItem, data)

    def get_instruments(self) -> list[TradeableInstrument]:
        """Fetch all tradeable instruments."""
        data = self._make_request("GET", "/equity/metadata/instruments")
        return parse_response(list[TradeableInstrument], data)

    def get_exchanges(self) -> list[Exchange]:
        """Fetch all exchanges and their working schedules."""
        data = self._make_request("GET", "/equity/metadata/exchanges")
        return parse_response(list[Exchange], data)

    def place_market_order(self, order_data: MarketRequest) -> Order:
        """Place a market order."""
        data = self._make_request(
            "POST",
            "/equity/orders/market",
            json=order_data.model_dump(mode="json", exclude_none=True),
        )
        return parse_response(Order, data)

    def place_limit_order(self, order_data: LimitRequest) -> Order:
        """Place a limit order."""
        data = self._make_request(
            "POST",
            "/equity/orders/limit",
            json=order_data.model_dump(mode="json", exclude_none=True),
        )
        return parse_response(Order, data)

    def place_stop_order(self, order_data: StopRequest) -> Order:
        """Place a stop order."""
        data = self._make_request(
            "POST",
            "/equity/orders/stop",
            json=order_data.model_dump(mode="json", exclude_none=True),
        )
        return parse_response(Order, data)

    def place_stop_limit_order(self, order_data: StopLimitRequest) -> Order:
        """Place a stop-limit order."""
        data = self._make_request(
            "POST",
            "/equity/orders/stop_limit",
            json=order_data.model_dump(mode="json", exclude_none=True),
        )
        return parse_response(Order, data)

    def cancel_order(self, order_id: int) -> None:
        """Cancel an existing order."""
        self._make_request("DELETE", f"/equity/orders/{order_id}")

    def get_reports(self) -> list[ReportResponse]:
        """Get account export reports."""
        data = self._make_request("GET", "/equity/history/exports")
        return parse_response(list[ReportResponse], data)

    def request_export(
        self,
        data_included: ReportDataIncluded | None = None,
        time_from: str | None = None,
        time_to: str | None = None,
    ) -> EnqueuedReportResponse:
        """Request a CSV export of the account history."""
        validated = PublicReportRequest.model_validate(
            {
                "dataIncluded": data_included or ReportDataIncluded(),
                "timeFrom": time_from,
                "timeTo": time_to,
            }
        )
        data_included = validated.dataIncluded or ReportDataIncluded()
        payload: dict[str, Any] = {
            "dataIncluded": data_included.model_dump(mode="json", exclude_none=True),
        }
        if time_from:
            payload["timeFrom"] = time_from
        if time_to:
            payload["timeTo"] = time_to

        data = self._make_request("POST", "/equity/history/exports", json=payload)
        return parse_response(EnqueuedReportResponse, data)
