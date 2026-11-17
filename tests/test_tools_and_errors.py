"""Tool-level behaviour, error codes and retry timing, with a mock API."""

import asyncio
from datetime import UTC, datetime
from email.utils import format_datetime

import httpx
import pytest
from mcp import Client

from trading212_mcp import client as client_module
from trading212_mcp.client import Trading212Client
from trading212_mcp.errors import UpstreamError
from trading212_mcp.models import LimitRequest, LimitRequestTimeValidityEnum
from trading212_mcp.server import create_server

INSTRUMENTS = [
    {"ticker": "AAPLE_XX_EQ", "name": "Not Apple"},
    {"ticker": "XAAPL_US_EQ", "name": "Contains the ticker"},
    {"ticker": "AAPL_US_EQ", "name": "Apple"},
    {"ticker": "MSFT_US_EQ", "name": "Microsoft"},
    {"ticker": "PINE_US_EQ", "name": "Pineapple Holdings"},
]
EXCHANGES = [
    {"id": 1, "name": "NASDAQ", "workingSchedules": []},
    {"id": 12, "name": "London Stock Exchange", "workingSchedules": []},
]


def call_tool(settings, name, args):
    def api(req):
        if req.url.path.endswith("/instruments"):
            return httpx.Response(200, json=INSTRUMENTS)
        return httpx.Response(200, json=EXCHANGES)

    server = create_server(
        settings,
        lambda s: Trading212Client(s, transport=httpx.MockTransport(api)),
    )

    async def run():
        async with Client(server) as session:
            result = await session.call_tool(name, args)
            assert not result.is_error
            return result.structured_content["result"]

    return asyncio.run(run())


def tickers(items):
    return [item["ticker"] for item in items]


def test_search_instrument_ranks_exact_then_prefix_then_contains(settings):
    found = call_tool(settings, "search_instrument", {"search_term": "aapl"})
    assert tickers(found) == ["AAPL_US_EQ", "AAPLE_XX_EQ", "XAAPL_US_EQ"]


def test_search_instrument_matches_names(settings):
    # An exact name match ranks first; partial name matches keep upstream order.
    found = call_tool(settings, "search_instrument", {"search_term": "apple"})
    assert tickers(found) == ["AAPL_US_EQ", "AAPLE_XX_EQ", "PINE_US_EQ"]


def test_search_instrument_exact_full_ticker(settings):
    found = call_tool(settings, "search_instrument", {"search_term": "MSFT_US_EQ"})
    assert tickers(found) == ["MSFT_US_EQ"]


@pytest.mark.parametrize(
    "args,expected",
    [
        ({"search_term": "aapl", "limit": 1}, 1),
        ({"limit": 2}, 2),
        ({"limit": 0}, 1),  # clamped to at least one result
        ({}, len(INSTRUMENTS)),
    ],
)
def test_search_instrument_limit(settings, args, expected):
    assert len(call_tool(settings, "search_instrument", args)) == expected


@pytest.mark.parametrize(
    "term,expected",
    [("london", [12]), ("12", [12]), ("1", [1]), ("", [1, 12]), ("none", [])],
)
def test_search_exchange_by_name_or_exact_id(settings, term, expected):
    found = call_tool(settings, "search_exchange", {"search_term": term})
    assert [item["id"] for item in found] == expected


def order_rejected(settings, status, body):
    transport = httpx.MockTransport(lambda req: httpx.Response(status, **body))
    request = LimitRequest(
        ticker="AAPL_US_EQ",
        quantity=1,
        limitPrice=1,
        timeValidity=LimitRequestTimeValidityEnum.DAY,
    )
    with Trading212Client(settings, transport=transport) as client:
        with pytest.raises(UpstreamError) as raised:
            client.place_limit_order(request)
    return str(raised.value)


def test_order_rejection_reports_safe_code_only(settings):
    message = order_rejected(
        settings,
        400,
        {
            "json": {
                "code": "InsufficientFreeForStocksBuy",
                "clarification": "secret upstream detail",
            }
        },
    )
    assert message == (
        "Trading 212 request failed (HTTP 400, code InsufficientFreeForStocksBuy)."
    )


@pytest.mark.parametrize(
    "body",
    [
        {"json": {"code": "has spaces <script>"}},
        {"json": {"code": "x" * 65}},
        {"json": {"code": 42}},
        {"json": ["InsufficientFreeForStocksBuy"]},
        {"json": {"clarification": "no code"}},
        {"content": b"not json"},
        {"content": b""},
    ],
)
def test_order_rejection_without_safe_code(settings, body):
    message = order_rejected(settings, 400, body)
    assert message == "Trading 212 request failed (HTTP 400)."


def test_server_errors_never_report_codes(settings):
    message = order_rejected(settings, 500, {"json": {"code": "Internal"}})
    assert message == "Trading 212 request failed (HTTP 500)."


@pytest.fixture
def frozen_time(monkeypatch):
    now = 1_800_000_000.0
    monkeypatch.setattr(client_module.time, "time", lambda: now)
    return now


@pytest.mark.parametrize(
    "headers,expected",
    [
        ({"retry-after": "7"}, 7),
        ({"retry-after": "-3"}, 0),
        ({"x-ratelimit-reset": "1800000004"}, 4),
        ({"x-ratelimit-reset": "1700000000"}, 0),
        # Unparseable values fall through to the next source, then to backoff.
        ({"retry-after": "soon", "x-ratelimit-reset": "1800000005"}, 5),
        ({"x-ratelimit-reset": "later"}, 4),
        ({}, 4),
    ],
)
def test_retry_delay_sources(frozen_time, headers, expected):
    response = httpx.Response(429, headers=headers)
    assert Trading212Client._retry_delay(response, 2) == expected


def test_retry_delay_http_date(frozen_time):
    when = datetime.fromtimestamp(frozen_time + 9, UTC)
    response = httpx.Response(429, headers={"retry-after": format_datetime(when, True)})
    assert Trading212Client._retry_delay(response, 0) == 9
