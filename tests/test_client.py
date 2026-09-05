"""Endpoint contracts: methods, paths, parameters, and serialized bodies."""

import httpx
import pytest
from pydantic import ValidationError

from trading212_mcp.client import Trading212Client
from trading212_mcp.errors import (
    AuthenticationError,
    InvalidResponseError,
    RateLimitError,
    RequestError,
    UpstreamError,
)
from trading212_mcp.models import (
    DuplicateBucketRequest,
    HistoryTransactionItem,
    LimitRequest,
    MarketRequest,
    Order,
    PieRequest,
    StopLimitRequest,
    StopRequest,
)

ORDER = {"ticker": "AAPL_US_EQ", "quantity": -1, "timeValidity": "DAY"}
CASES = [
    ("get_account_summary", (), "GET", "/equity/account/summary", {"currency": "GBP"}),
    (
        "get_account_cash",
        (),
        "GET",
        "/equity/account/summary",
        {"cash": {"availableToTrade": 12}},
    ),
    ("get_account_positions", (), "GET", "/equity/positions", []),
    ("get_positions", ("AAPL_US_EQ",), "GET", "/equity/positions", []),
    (
        "get_position_by_ticker",
        ("AAPL_US_EQ",),
        "GET",
        "/equity/positions",
        [{"quantity": 2}],
    ),
    (
        "get_account_position_by_ticker",
        ("AAPL_US_EQ",),
        "GET",
        "/equity/positions",
        [{"quantity": 2}],
    ),
    (
        "search_position_by_ticker",
        ("AAPL_US_EQ",),
        "GET",
        "/equity/positions",
        [{"quantity": 2}],
    ),
    (
        "get_dividends",
        (100, "AAPL_US_EQ", 500),
        "GET",
        "/equity/history/dividends",
        {"items": [], "nextPagePath": "/api/v0/equity/history/dividends?cursor=200"},
    ),
    ("get_orders", (), "GET", "/equity/orders", []),
    ("get_order_by_id", (12,), "GET", "/equity/orders/12", {"id": 12}),
    ("get_pies", (), "GET", "/equity/pies", []),
    ("get_pie_by_id", (12,), "GET", "/equity/pies/12", {}),
    (
        "create_pie",
        (PieRequest(name="Test", instrumentShares={"AAPL_US_EQ": 1}),),
        "POST",
        "/equity/pies",
        {},
    ),
    ("update_pie", (12, PieRequest()), "POST", "/equity/pies/12", {}),
    (
        "duplicate_pie",
        (12, DuplicateBucketRequest(name="Copy")),
        "POST",
        "/equity/pies/12/duplicate",
        {},
    ),
    ("delete_pie", (12,), "DELETE", "/equity/pies/12", None),
    (
        "get_historical_order_data",
        (100, "AAPL_US_EQ", 50),
        "GET",
        "/equity/history/orders",
        {"items": []},
    ),
    (
        "get_history_transactions",
        ("abc", "2025-01-01T00:00:00Z", 20),
        "GET",
        "/equity/history/transactions",
        {"items": []},
    ),
    (
        "get_instruments",
        (),
        "GET",
        "/equity/metadata/instruments",
        [{"ticker": "AAPL_US_EQ", "name": "Apple"}],
    ),
    (
        "get_exchanges",
        (),
        "GET",
        "/equity/metadata/exchanges",
        [{"id": 1, "name": "Test", "workingSchedules": []}],
    ),
    (
        "place_market_order",
        (MarketRequest(ticker="AAPL_US_EQ", quantity=-1),),
        "POST",
        "/equity/orders/market",
        {"id": 1},
    ),
    (
        "place_limit_order",
        (LimitRequest(**ORDER, limitPrice=10),),
        "POST",
        "/equity/orders/limit",
        {"id": 1},
    ),
    (
        "place_stop_order",
        (StopRequest(**ORDER, stopPrice=10),),
        "POST",
        "/equity/orders/stop",
        {"id": 1},
    ),
    (
        "place_stop_limit_order",
        (StopLimitRequest(**ORDER, stopPrice=10, limitPrice=9),),
        "POST",
        "/equity/orders/stop_limit",
        {"id": 1},
    ),
    ("cancel_order", (12,), "DELETE", "/equity/orders/12", None),
    ("get_reports", (), "GET", "/equity/history/exports", []),
    ("request_export", (), "POST", "/equity/history/exports", {"reportId": 1}),
]


@pytest.mark.parametrize("method,args,verb,path,response", CASES)
def test_endpoint(settings, method, args, verb, path, response):
    calls = []

    def respond(req):
        calls.append(req)
        return (
            httpx.Response(204)
            if response is None
            else httpx.Response(200, json=response)
        )

    with Trading212Client(settings, transport=httpx.MockTransport(respond)) as c:
        result = getattr(c, method)(*args)
    req = calls[0]
    assert req.method == verb and req.url.path == "/api/v0" + path
    assert len(calls) == 1
    if method in (
        "get_positions",
        "get_position_by_ticker",
        "get_account_position_by_ticker",
        "search_position_by_ticker",
    ):
        assert req.url.params["ticker"] == "AAPL_US_EQ"
    if method == "get_dividends":
        assert req.url.params == httpx.QueryParams(
            cursor=100, ticker="AAPL_US_EQ", limit=50
        )
        assert result.nextPagePath.endswith("cursor=200")
    if method.startswith("place_"):
        import json

        assert json.loads(req.content) == args[0].model_dump(
            mode="json", exclude_none=True
        )
    if method == "request_export":
        import json

        assert json.loads(req.content) == {
            "dataIncluded": {
                "includeDividends": True,
                "includeInterest": True,
                "includeOrders": True,
                "includeTransactions": True,
            }
        }


@pytest.mark.parametrize(
    "status,error",
    [
        (401, AuthenticationError),
        (403, AuthenticationError),
        (429, RateLimitError),
        (500, UpstreamError),
        (302, UpstreamError),
        (400, UpstreamError),
    ],
)
def test_errors_and_retry_limit(settings, status, error):
    calls = []
    sleeps = []

    def respond(req):
        calls.append(req)
        return httpx.Response(
            status,
            headers={"location": "https://evil.invalid/"},
            text="synthetic-account-private-data",
        )

    with Trading212Client(
        settings, transport=httpx.MockTransport(respond), sleep=sleeps.append
    ) as c:
        with pytest.raises(error) as exc:
            c.get_orders()
    assert "synthetic-account-private-data" not in str(exc.value)
    assert len(calls) == (3 if status in (429, 500) else 1)


def test_retry_then_success_and_reset_budget(settings):
    calls = []
    sleeps = []

    def respond(req):
        calls.append(req)
        return httpx.Response(
            503 if len(calls) < 3 else 200, headers={"retry-after": "2"}, json=[]
        )

    with Trading212Client(
        settings, transport=httpx.MockTransport(respond), sleep=sleeps.append
    ) as c:
        assert c.get_orders() == []
    assert sleeps == [2, 2]
    with Trading212Client(
        settings.model_copy(update={"account_ttl": 0}),
        transport=httpx.MockTransport(
            lambda req: httpx.Response(429, headers={"retry-after": "60"})
        ),
        sleep=sleeps.append,
    ) as c:
        with pytest.raises(RateLimitError):
            c.get_orders()
    assert sleeps == [2, 2]


def test_invalid_json_and_missing_position(settings):
    with Trading212Client(
        settings,
        transport=httpx.MockTransport(lambda req: httpx.Response(200, text="not-json")),
    ) as c:
        with pytest.raises(InvalidResponseError):
            c.get_orders()
    with Trading212Client(
        settings,
        transport=httpx.MockTransport(lambda req: httpx.Response(200, json=[])),
    ) as c:
        with pytest.raises(RequestError, match="No open position"):
            c.get_position_by_ticker("AAPL_US_EQ")


@pytest.mark.parametrize(
    "path",
    [
        "https://evil.invalid/",
        "//evil.invalid/",
        "/equity/../secret",
        "/equity/%2e%2e/secret",
        "/api/v1/equity/orders",
        "/equity/a\\b",
        "/equity/orders#fragment",
        "/equity/orders\n",
        "/other",
    ],
)
def test_rejects_unsafe_paths(settings, path):
    with Trading212Client(settings) as c:
        with pytest.raises(RequestError):
            c._make_request("GET", path)


def test_pagination_path_and_auth(settings):
    calls = []
    with Trading212Client(
        settings,
        transport=httpx.MockTransport(
            lambda req: calls.append(req) or httpx.Response(200, json={})
        ),
    ) as c:
        c._make_request("GET", "/api/v0/equity/history/orders?cursor=123&limit=2")
    assert calls[0].url.params["cursor"] == "123"
    assert calls[0].headers["Authorization"].startswith("Basic ")
    with Trading212Client(
        settings.model_copy(update={"api_secret": None}),
        transport=httpx.MockTransport(
            lambda req: calls.append(req) or httpx.Response(200, json={})
        ),
    ) as c:
        c._make_request("GET", "/equity/orders")
    assert calls[1].headers["Authorization"] == "synthetic-key"


@pytest.mark.parametrize("quantity", [0, float("nan"), float("inf"), float("-inf")])
def test_invalid_quantity(quantity):
    with pytest.raises(ValidationError):
        MarketRequest(ticker="AAPL_US_EQ", quantity=quantity)


@pytest.mark.parametrize("price", [0, -1, float("nan"), float("inf")])
def test_invalid_price(price):
    with pytest.raises(ValidationError):
        LimitRequest(**ORDER, limitPrice=price)


def test_invalid_ticker_and_export_dates(settings):
    with pytest.raises(ValidationError):
        MarketRequest(ticker="", quantity=1)
    with Trading212Client(settings) as c:
        with pytest.raises(ValidationError):
            c.request_export(time_from="not a date")
        with pytest.raises(ValidationError):
            c.request_export(
                time_from="2025-02-01T00:00:00Z", time_to="2025-01-01T00:00:00Z"
            )
        with pytest.raises(ValidationError):
            c.request_export(time_from="2025-01-01")


def test_current_upstream_enum_values():
    free_cash = HistoryTransactionItem(type="INTEREST_ON_FREE_CASH")
    lending = HistoryTransactionItem(type="LENDING_INTEREST")
    autoinvest = Order(initiatedFrom="INSTRUMENT_AUTOINVEST")
    assert free_cash.type.value == "INTEREST_ON_FREE_CASH"
    assert lending.type.value == "LENDING_INTEREST"
    assert autoinvest.initiatedFrom.value == "INSTRUMENT_AUTOINVEST"


def test_wrong_response_shape_is_typed_error(settings):
    with Trading212Client(
        settings,
        transport=httpx.MockTransport(lambda req: httpx.Response(200, json={})),
    ) as c:
        with pytest.raises(InvalidResponseError):
            c.get_orders()


def test_export_dates_serialization(settings):
    calls = []
    with Trading212Client(
        settings,
        transport=httpx.MockTransport(
            lambda req: calls.append(req) or httpx.Response(200, json={"reportId": 1})
        ),
    ) as c:
        c.request_export(
            time_from="2025-01-01T00:00:00Z", time_to="2025-02-01T00:00:00Z"
        )
    import json

    assert json.loads(calls[0].content)["timeTo"] == "2025-02-01T00:00:00Z"
