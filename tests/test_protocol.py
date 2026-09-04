"""Compatibility checks through real MCP protocol sessions, with a mock API."""

import asyncio
import json
from pathlib import Path

import httpx
from mcp import Client

from trading212_mcp.cache import META_KEY
from trading212_mcp.client import Trading212Client
from trading212_mcp.server import create_server

BASELINE = json.loads((Path(__file__).parent / "fixtures/mcp_v1.json").read_text())


def test_overlapping_sessions_keep_shared_client_alive(settings):
    clients = []

    def factory(settings):
        client = Trading212Client(settings, transport=httpx.MockTransport(api_response))
        clients.append(client)
        return client

    server = create_server(settings, factory)

    async def run():
        async with Client(server) as first:
            async with Client(server) as second:
                assert not (await first.call_tool("fetch_all_orders", {})).is_error
                assert not (await second.call_tool("fetch_all_orders", {})).is_error
                assert len(clients) == 1
            assert not clients[0].cache.closed
            assert not (await first.call_tool("fetch_all_orders", {})).is_error
            assert (await first.read_resource("trading212://orders")).contents
        assert clients[0].cache.closed
        async with Client(server) as restarted:
            assert not (await restarted.call_tool("fetch_all_orders", {})).is_error
            assert len(clients) == 2
        assert clients[1].cache.closed

    asyncio.run(run())


def api_response(req):
    path = req.url.path
    if path.endswith("/summary"):
        data = {"id": 1, "currency": "GBP", "cash": {"availableToTrade": 100}}
    elif path.endswith("/positions"):
        data = [{"quantity": 2, "instrument": {"ticker": "AAPL_US_EQ"}}]
    elif path.endswith("/instruments"):
        data = [{"ticker": "AAPL_US_EQ", "name": "Apple"}]
    elif path.endswith("/exchanges"):
        data = [{"id": 1, "name": "Test", "workingSchedules": []}]
    elif path.endswith("/exports"):
        data = [] if req.method == "GET" else {"reportId": 1}
    elif "/history/" in path:
        data = {"items": [], "nextPagePath": None}
    elif path.endswith(("/orders", "/pies")) and req.method == "GET":
        data = []
    else:
        data = {"id": 1}
    return (
        httpx.Response(204)
        if req.method == "DELETE"
        else httpx.Response(200, json=data)
    )


def test_full_protocol_surface_and_lifecycle(settings):
    clients = []

    def factory(settings):
        c = Trading212Client(settings, transport=httpx.MockTransport(api_response))
        clients.append(c)
        return c

    server = create_server(settings, factory)
    assert clients == []

    async def run():
        async with Client(server) as session:
            tools = (await session.list_tools()).tools
            assert {t.name for t in tools} == {t["name"] for t in BASELINE["tools"]}
            values = {
                "ticker": "AAPL_US_EQ",
                "quantity": -1,
                "limit_price": 10,
                "stop_price": 10,
                "pie_id": 1,
                "order_id": 1,
                "name": "Test",
                "instrument_shares": {"AAPL_US_EQ": 1},
            }
            for tool in tools:
                args = {
                    key: values[key] for key in tool.input_schema.get("required", [])
                }
                if tool.name == "update_pie":
                    args["name"] = "Updated"
                result = await session.call_tool(tool.name, args)
                assert not result.is_error, (tool.name, result)
                assert META_KEY in result.meta
                assert tool.annotations is not None
                baseline = next(t for t in BASELINE["tools"] if t["name"] == tool.name)
                required = set(baseline["inputSchema"].get("required", []))
                if tool.name == "update_pie":
                    required.add("name")
                assert set(tool.input_schema.get("required", [])) == required
                assert set(tool.input_schema["properties"]) == set(
                    baseline["inputSchema"]["properties"]
                )
            resources = (await session.list_resources()).resources
            assert {str(r.uri) for r in resources} == {
                r["uri"] for r in BASELINE["resources"]
            }
            for resource in resources:
                result = await session.read_resource(resource.uri)
                assert result.contents and META_KEY in result.contents[0].meta
            templates = (await session.list_resource_templates()).resource_templates
            assert {r.uri_template for r in templates} == {
                r["uriTemplate"] for r in BASELINE["templates"]
            }
            for template in templates:
                uri = (
                    template.uri_template.replace("{ticker}", "AAPL_US_EQ")
                    .replace("{order_id}", "1")
                    .replace("{pie_id}", "1")
                )
                result = await session.read_resource(uri)
                assert result.contents
            prompt = await session.get_prompt("analyse_trading212_data", {})
            assert "GBP" in prompt.messages[0].content.text
            first = await session.call_tool("fetch_account_summary", {})
            second = await session.call_tool("fetch_account_summary", {})
            assert first.structured_content == second.structured_content
            assert second.meta[META_KEY][0]["cacheHit"] is True
            invalid = await session.call_tool(
                "place_market_order", {"ticker": "AAPL_US_EQ", "quantity": 0}
            )
            assert invalid.is_error

    asyncio.run(run())
    assert clients[0].http.is_closed and clients[0].cache.closed


def test_prompt_failure_has_no_stdout_or_private_errors(settings, capsys):
    def factory(settings):
        return Trading212Client(
            settings,
            transport=httpx.MockTransport(
                lambda req: httpx.Response(401, text="SENSITIVE BODY")
            ),
        )

    async def run():
        async with Client(create_server(settings, factory)) as session:
            prompt = await session.get_prompt("analyse_trading212_data", {})
            assert "GBX" in prompt.messages[0].content.text
            result = await session.call_tool("fetch_account_summary", {})
            assert result.is_error
            assert "SENSITIVE BODY" not in str(result)

    asyncio.run(run())
    assert capsys.readouterr().out == ""
