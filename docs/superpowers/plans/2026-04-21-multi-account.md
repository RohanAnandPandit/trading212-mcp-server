# Multi-Account Support Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend the Trading212 MCP server so multiple named Trading212 accounts can be configured in `accounts.json` and queried individually, in subsets, or all at once via an optional `account` parameter on every tool.

**Architecture:** A new `AccountRegistry` class loads `accounts.json` at startup and caches one `Trading212Client` per account. A `resolve` method on the registry fans out to the right client(s) based on the `account` param value (`None` → default, `"all"` → all, string/list → named accounts). All read tools gain an optional `account` param; write tools gain a required one. A `format_response` helper shapes single-account results identically to today and multi-account results as a labelled list with optional numeric totals.

**Tech Stack:** Python 3.11+, FastMCP, Pydantic v2, pytest, pytest-mock

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `src/accounts.py` | Create | `AccountRegistry` class — loads config, caches clients, resolves account selectors |
| `src/utils/response.py` | Create | `format_response` — shapes single/multi-account responses, computes totals |
| `src/mcp_server.py` | Modify | Replace global `client` with `registry`; expose `registry` to tools |
| `src/tools.py` | Modify | Add `account` param to all tools; add `list_accounts` tool |
| `src/config.py` | Modify | Add `ACCOUNTS_CONFIG` env var constant |
| `accounts.json.example` | Create | Template users copy to `accounts.json` |
| `tests/__init__.py` | Create | Make tests a package |
| `tests/test_accounts.py` | Create | Tests for `AccountRegistry` |
| `tests/test_response.py` | Create | Tests for `format_response` |

---

## Task 1: Set up test infrastructure

**Files:**
- Create: `tests/__init__.py`
- Modify: `pyproject.toml`

- [ ] **Step 1: Add pytest and pytest-mock to pyproject.toml**

Edit `pyproject.toml` so `[project]` has an optional-dependencies section:

```toml
[project]
name = "trading212-mcp-server"
version = "0.1.0"
description = "Add your description here"
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
    "hishel>=0.1.2",
    "httpx>=0.28.1",
    "mcp[cli]>=1.8.0",
    "pydantic>=2.11.4",
    "python-dotenv>=1.1.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-mock>=3.14.0",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
```

- [ ] **Step 2: Install dev dependencies**

```bash
uv pip install pytest pytest-mock
```

Expected: packages install without error.

- [ ] **Step 3: Create tests package**

Create `tests/__init__.py` as an empty file.

- [ ] **Step 4: Verify pytest discovers tests directory**

```bash
uv run pytest tests/ --collect-only
```

Expected output contains: `no tests ran` (no tests yet, but no import errors).

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml tests/__init__.py
git commit -m "chore: add pytest infrastructure for multi-account feature"
```

---

## Task 2: Create AccountRegistry

**Files:**
- Create: `src/accounts.py`
- Create: `tests/test_accounts.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_accounts.py`:

```python
import json
import os
import pytest
from unittest.mock import patch, MagicMock


def make_config(tmp_path, accounts, default):
    config = {"default": default, "accounts": accounts}
    p = tmp_path / "accounts.json"
    p.write_text(json.dumps(config))
    return str(p)


@patch("accounts.Trading212Client")
def test_loads_accounts_from_file(MockClient, tmp_path):
    path = make_config(tmp_path, [
        {"name": "sumeet", "api_key": "k1", "api_secret": "s1", "environment": "live"},
        {"name": "wife",   "api_key": "k2", "api_secret": "s2", "environment": "live"},
    ], default="sumeet")

    from accounts import AccountRegistry
    registry = AccountRegistry(config_path=path)

    assert registry.account_names() == ["sumeet", "wife"]
    assert registry.default_name() == "sumeet"
    assert MockClient.call_count == 2


@patch("accounts.Trading212Client")
def test_get_client_returns_correct_instance(MockClient, tmp_path):
    mock_sumeet = MagicMock()
    mock_wife = MagicMock()
    MockClient.side_effect = [mock_sumeet, mock_wife]

    path = make_config(tmp_path, [
        {"name": "sumeet", "api_key": "k1", "api_secret": "s1", "environment": "live"},
        {"name": "wife",   "api_key": "k2", "api_secret": "s2", "environment": "live"},
    ], default="sumeet")

    from accounts import AccountRegistry
    registry = AccountRegistry(config_path=path)

    assert registry.get_client("sumeet") is mock_sumeet
    assert registry.get_client("wife") is mock_wife


@patch("accounts.Trading212Client")
def test_get_client_raises_on_unknown_account(MockClient, tmp_path):
    path = make_config(tmp_path, [
        {"name": "sumeet", "api_key": "k1", "api_secret": "s1", "environment": "live"},
    ], default="sumeet")

    from accounts import AccountRegistry
    registry = AccountRegistry(config_path=path)

    with pytest.raises(ValueError, match="Account 'xyz' not found"):
        registry.get_client("xyz")


@patch("accounts.Trading212Client")
def test_all_clients_returns_all(MockClient, tmp_path):
    path = make_config(tmp_path, [
        {"name": "sumeet", "api_key": "k1", "api_secret": "s1", "environment": "live"},
        {"name": "wife",   "api_key": "k2", "api_secret": "s2", "environment": "live"},
    ], default="sumeet")

    from accounts import AccountRegistry
    registry = AccountRegistry(config_path=path)

    all_clients = registry.all_clients()
    assert set(all_clients.keys()) == {"sumeet", "wife"}


@patch("accounts.Trading212Client")
def test_resolve_none_returns_default(MockClient, tmp_path):
    path = make_config(tmp_path, [
        {"name": "sumeet", "api_key": "k1", "api_secret": "s1", "environment": "live"},
        {"name": "wife",   "api_key": "k2", "api_secret": "s2", "environment": "live"},
    ], default="sumeet")

    from accounts import AccountRegistry
    registry = AccountRegistry(config_path=path)

    result = registry.resolve(None)
    assert list(result.keys()) == ["sumeet"]


@patch("accounts.Trading212Client")
def test_resolve_all_returns_all_accounts(MockClient, tmp_path):
    path = make_config(tmp_path, [
        {"name": "sumeet", "api_key": "k1", "api_secret": "s1", "environment": "live"},
        {"name": "wife",   "api_key": "k2", "api_secret": "s2", "environment": "live"},
    ], default="sumeet")

    from accounts import AccountRegistry
    registry = AccountRegistry(config_path=path)

    result = registry.resolve("all")
    assert set(result.keys()) == {"sumeet", "wife"}


@patch("accounts.Trading212Client")
def test_resolve_string_returns_named_account(MockClient, tmp_path):
    path = make_config(tmp_path, [
        {"name": "sumeet", "api_key": "k1", "api_secret": "s1", "environment": "live"},
        {"name": "wife",   "api_key": "k2", "api_secret": "s2", "environment": "live"},
    ], default="sumeet")

    from accounts import AccountRegistry
    registry = AccountRegistry(config_path=path)

    result = registry.resolve("wife")
    assert list(result.keys()) == ["wife"]


@patch("accounts.Trading212Client")
def test_resolve_list_returns_subset(MockClient, tmp_path):
    path = make_config(tmp_path, [
        {"name": "sumeet", "api_key": "k1", "api_secret": "s1", "environment": "live"},
        {"name": "wife",   "api_key": "k2", "api_secret": "s2", "environment": "live"},
        {"name": "son",    "api_key": "k3", "api_secret": "s3", "environment": "demo"},
    ], default="sumeet")

    from accounts import AccountRegistry
    registry = AccountRegistry(config_path=path)

    result = registry.resolve(["wife", "son"])
    assert set(result.keys()) == {"wife", "son"}


@patch("accounts.Trading212Client")
def test_fallback_to_env_vars_when_no_config_file(MockClient):
    with patch.dict(os.environ, {
        "TRADING212_API_KEY": "envkey",
        "TRADING212_API_SECRET": "envsecret",
        "ENVIRONMENT": "live",
    }):
        from accounts import AccountRegistry
        registry = AccountRegistry(config_path="/nonexistent/path/accounts.json")

    assert registry.default_name() == "default"
    assert "default" in registry.account_names()
    MockClient.assert_called_once_with(
        api_key="envkey", api_secret="envsecret", environment="live"
    )


def test_raises_when_no_config_and_no_env_vars():
    with patch.dict(os.environ, {}, clear=True):
        # Ensure these env vars are absent
        for key in ["TRADING212_API_KEY", "TRADING212_API_SECRET"]:
            os.environ.pop(key, None)

        from accounts import AccountRegistry
        with pytest.raises(ValueError, match="No accounts configured"):
            AccountRegistry(config_path="/nonexistent/path/accounts.json")
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
uv run pytest tests/test_accounts.py -v
```

Expected: `ModuleNotFoundError: No module named 'accounts'`

- [ ] **Step 3: Create src/accounts.py**

```python
import json
import os
from typing import Union
from utils.client import Trading212Client


class AccountRegistry:
    def __init__(self, config_path: str = None):
        config_path = config_path or os.getenv("ACCOUNTS_CONFIG", "accounts.json")
        self._clients: dict[str, Trading212Client] = {}
        self._default: str = None

        if os.path.exists(config_path):
            self._load_from_file(config_path)
        else:
            self._load_from_env()

    def _load_from_file(self, config_path: str) -> None:
        with open(config_path) as f:
            config = json.load(f)

        self._default = config["default"]
        for account in config["accounts"]:
            self._clients[account["name"]] = Trading212Client(
                api_key=account["api_key"],
                api_secret=account["api_secret"],
                environment=account["environment"],
            )

    def _load_from_env(self) -> None:
        api_key = os.getenv("TRADING212_API_KEY")
        api_secret = os.getenv("TRADING212_API_SECRET")
        environment = os.getenv("ENVIRONMENT", "demo")

        if not api_key or not api_secret:
            raise ValueError(
                "No accounts configured. Create accounts.json or set "
                "TRADING212_API_KEY and TRADING212_API_SECRET."
            )

        self._clients = {
            "default": Trading212Client(
                api_key=api_key, api_secret=api_secret, environment=environment
            )
        }
        self._default = "default"

    def get_client(self, name: str) -> Trading212Client:
        if name not in self._clients:
            available = ", ".join(self._clients.keys())
            raise ValueError(
                f"Account '{name}' not found. Available accounts: {available}"
            )
        return self._clients[name]

    def get_clients(self, names: list[str]) -> dict[str, Trading212Client]:
        return {name: self.get_client(name) for name in names}

    def all_clients(self) -> dict[str, Trading212Client]:
        return dict(self._clients)

    def account_names(self) -> list[str]:
        return list(self._clients.keys())

    def default_name(self) -> str:
        return self._default

    def resolve(self, account: Union[str, list[str], None]) -> dict[str, Trading212Client]:
        if account is None:
            return {self._default: self._clients[self._default]}
        if account == "all":
            return self.all_clients()
        if isinstance(account, list):
            return self.get_clients(account)
        return {account: self.get_client(account)}
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
uv run pytest tests/test_accounts.py -v
```

Expected: all 10 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/accounts.py tests/test_accounts.py
git commit -m "feat: add AccountRegistry with multi-account config and resolve logic"
```

---

## Task 3: Create format_response helper

**Files:**
- Create: `src/utils/response.py`
- Create: `tests/test_response.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_response.py`:

```python
import pytest
from utils.response import format_response


def test_single_account_returns_data_directly():
    data = {"free": 100.0, "invested": 500.0}
    result = format_response({"sumeet": data})
    assert result == data


def test_multi_account_returns_labelled_list():
    result = format_response({
        "sumeet": {"free": 100.0},
        "wife": {"free": 200.0},
    })
    assert result == [
        {"account": "sumeet", "data": {"free": 100.0}},
        {"account": "wife",   "data": {"free": 200.0}},
    ]


def test_multi_account_with_totals():
    result = format_response(
        {
            "sumeet": {"free": 100.0, "invested": 500.0, "total": 600.0},
            "wife":   {"free": 200.0, "invested": 300.0, "total": 500.0},
        },
        compute_totals=True,
    )
    assert {"account": "sumeet", "data": {"free": 100.0, "invested": 500.0, "total": 600.0}} in result
    assert {"account": "wife",   "data": {"free": 200.0, "invested": 300.0, "total": 500.0}} in result
    totals_entry = next(e for e in result if e["account"] == "__totals__")
    assert totals_entry["data"]["free"] == pytest.approx(300.0)
    assert totals_entry["data"]["invested"] == pytest.approx(800.0)
    assert totals_entry["data"]["total"] == pytest.approx(1100.0)


def test_partial_failure_included_as_error_entry():
    result = format_response({
        "sumeet": {"free": 100.0},
        "wife":   Exception("API rate limit"),
    })
    sumeet_entry = next(e for e in result if e["account"] == "sumeet")
    assert sumeet_entry["data"] == {"free": 100.0}

    wife_entry = next(e for e in result if e["account"] == "wife")
    assert "error" in wife_entry
    assert "API rate limit" in wife_entry["error"]


def test_pydantic_model_serialised_before_totals():
    from pydantic import BaseModel

    class Cash(BaseModel):
        free: float
        invested: float

    result = format_response(
        {"sumeet": Cash(free=50.0, invested=200.0)},
        compute_totals=True,
    )
    # Single account → returned directly as dict (Pydantic model serialised)
    assert result == {"free": 50.0, "invested": 200.0}


def test_single_account_totals_flag_ignored():
    # compute_totals on a single-account result still returns data directly
    data = {"free": 100.0, "invested": 500.0}
    result = format_response({"sumeet": data}, compute_totals=True)
    assert result == data
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
uv run pytest tests/test_response.py -v
```

Expected: `ModuleNotFoundError: No module named 'utils.response'`

- [ ] **Step 3: Create src/utils/response.py**

```python
from typing import Any, Union


def _to_dict(data: Any) -> dict:
    if hasattr(data, "model_dump"):
        return data.model_dump(mode="json")
    return data


def _compute_totals(data_dicts: list[dict]) -> dict:
    totals: dict[str, float] = {}
    for d in data_dicts:
        for key, value in d.items():
            if isinstance(value, (int, float)):
                totals[key] = totals.get(key, 0.0) + value
    return totals


def format_response(
    results: dict[str, Any],
    compute_totals: bool = False,
) -> Any:
    if len(results) == 1:
        data = next(iter(results.values()))
        if isinstance(data, Exception):
            name = next(iter(results.keys()))
            return {"account": name, "error": str(data)}
        return _to_dict(data)

    entries = []
    data_dicts_for_totals = []

    for account_name, data in results.items():
        if isinstance(data, Exception):
            entries.append({"account": account_name, "error": str(data)})
        else:
            serialised = _to_dict(data)
            entries.append({"account": account_name, "data": serialised})
            if compute_totals:
                data_dicts_for_totals.append(serialised)

    if compute_totals and data_dicts_for_totals:
        entries.append({"account": "__totals__", "data": _compute_totals(data_dicts_for_totals)})

    return entries
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
uv run pytest tests/test_response.py -v
```

Expected: all 6 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/utils/response.py tests/test_response.py
git commit -m "feat: add format_response helper for single and multi-account responses"
```

---

## Task 4: Update mcp_server.py

**Files:**
- Modify: `src/mcp_server.py`
- Modify: `src/config.py`

- [ ] **Step 1: Update src/config.py**

Replace the entire content of `src/config.py` with:

```python
import os
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

TRANSPORT = os.getenv("TRANSPORT", "stdio")
ACCOUNTS_CONFIG = os.getenv("ACCOUNTS_CONFIG", "accounts.json")
```

- [ ] **Step 2: Update src/mcp_server.py**

Replace the entire content of `src/mcp_server.py` with:

```python
from mcp.server.fastmcp import FastMCP
from dotenv import find_dotenv, load_dotenv
from accounts import AccountRegistry
from config import ACCOUNTS_CONFIG

load_dotenv(find_dotenv())

mcp = FastMCP(
    name="Trading212",
    dependencies=["hishel", "pydantic"],
    stateless_http=True,
    host="127.0.0.1",
    port=8000,
)

registry = AccountRegistry(config_path=ACCOUNTS_CONFIG)
```

- [ ] **Step 3: Verify server starts without error (requires accounts.json or env vars)**

If you have env vars set, run:

```bash
uv run python src/server.py &
sleep 2
kill %1
```

Expected: server starts and exits cleanly (no traceback).

If no env vars available, create a minimal `accounts.json` with real or placeholder values and verify `AccountRegistry` loads it by running:

```bash
uv run python -c "
import sys; sys.path.insert(0, 'src')
from accounts import AccountRegistry
import json, tempfile, os
cfg = {'default': 'test', 'accounts': [{'name': 'test', 'api_key': 'k', 'api_secret': 's', 'environment': 'demo'}]}
with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
    json.dump(cfg, f)
    path = f.name
r = AccountRegistry(config_path=path)
print('accounts:', r.account_names())
os.unlink(path)
"
```

Expected output: `accounts: ['test']`

- [ ] **Step 4: Commit**

```bash
git add src/mcp_server.py src/config.py
git commit -m "feat: replace single client with AccountRegistry in mcp_server"
```

---

## Task 5: Update read tools

**Files:**
- Modify: `src/tools.py`

Read tools are: `search_instrument`, `search_exchange`, `fetch_pies`, `fetch_a_pie`, `fetch_all_orders`, `fetch_order`, `fetch_account_info`, `fetch_account_cash`, `fetch_all_open_positions`, `fetch_open_position_by_ticker`, `search_specific_position_by_ticker`, `fetch_historical_order_data`, `fetch_paid_out_dividends`, `fetch_exports_list`, `fetch_transaction_list`.

- [ ] **Step 1: Update the import block at the top of src/tools.py**

Replace:
```python
from typing import Optional
from mcp_server import mcp, client

from models import *
```

With:
```python
from typing import Optional, Union
from mcp_server import mcp, registry

from models import *
from utils.response import format_response
```

- [ ] **Step 2: Update search_instrument**

Replace:
```python
@mcp.tool("search_instrument")
def search_instrument(search_term: str = None) -> list[TradeableInstrument]:
    """
    Fetch instruments, optionally filtered by ticker or name.

    Args:
        search_term: Search term to filter instruments by ticker or name
        (case-insensitive)

    Returns:
        List of matching TradeableInstrument objects, or all instruments if no
        search term is provided
    """
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
```

With:
```python
@mcp.tool("search_instrument")
def search_instrument(
    search_term: str = None,
    account: Union[str, list[str], None] = None,
) -> list[TradeableInstrument]:
    """
    Fetch instruments, optionally filtered by ticker or name.

    Args:
        search_term: Search term to filter instruments by ticker or name
        (case-insensitive)
        account: Account name, list of names, "all", or None for default account.
        Instrument data is market-wide; any account's credentials work.

    Returns:
        List of matching TradeableInstrument objects, or all instruments if no
        search term is provided
    """
    clients = registry.resolve(account)
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
```

- [ ] **Step 3: Update search_exchange**

Replace:
```python
@mcp.tool("search_exchange")
def search_exchange(search_term: str = None) -> list[Exchange]:
    """
    Fetch exchanges, optionally filtered by name or ID.

    Args:
        search_term: Optional search term to filter exchanges by name or ID
        (case-insensitive)

    Returns:
        List of matching Exchange objects, or all exchanges if no search term
        is provided
    """
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
```

With:
```python
@mcp.tool("search_exchange")
def search_exchange(
    search_term: str = None,
    account: Union[str, list[str], None] = None,
) -> list[Exchange]:
    """
    Fetch exchanges, optionally filtered by name or ID.

    Args:
        search_term: Optional search term to filter exchanges by name or ID
        (case-insensitive)
        account: Account name, list of names, "all", or None for default account.
        Exchange data is market-wide; any account's credentials work.

    Returns:
        List of matching Exchange objects, or all exchanges if no search term
        is provided
    """
    clients = registry.resolve(account)
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
```

- [ ] **Step 4: Update fetch_pies**

Replace:
```python
@mcp.tool("fetch_pies")
def fetch_pies() -> list[AccountBucketResultResponse]:
    """Fetch all pies."""
    return client.get_pies()
```

With:
```python
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
```

- [ ] **Step 5: Update fetch_a_pie**

Replace:
```python
@mcp.tool("fetch_a_pie")
def fetch_a_pie(pie_id: int) -> AccountBucketResultResponse:
    """Fetch a specific pie by ID."""
    return client.get_pie_by_id(pie_id)
```

With:
```python
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
```

- [ ] **Step 6: Update fetch_all_orders**

Replace:
```python
@mcp.tool("fetch_all_orders")
def fetch_orders() -> list[Order]:
    """Fetch all equity orders."""
    return client.get_orders()
```

With:
```python
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
```

- [ ] **Step 7: Update fetch_order**

Replace:
```python
@mcp.tool("fetch_order")
def fetch_order_by_id(order_id: int) -> Order:
    """Fetch a specific order by ID."""
    return client.get_order_by_id(order_id)
```

With:
```python
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
```

- [ ] **Step 8: Update fetch_account_info**

Replace:
```python
@mcp.tool("fetch_account_info")
def fetch_account_info() -> Account:
    """Fetch account metadata."""
    return client.get_account_info()
```

With:
```python
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
```

- [ ] **Step 9: Update fetch_account_cash**

Replace:
```python
@mcp.tool("fetch_account_cash")
def fetch_account_cash() -> Cash:
    """Fetch account cash balance."""
    return client.get_account_cash()
```

With:
```python
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
```

- [ ] **Step 10: Update fetch_all_open_positions**

Replace:
```python
@mcp.tool("fetch_all_open_positions")
def fetch_all_open_positions() -> list[Position]:
    """Fetch all open positions."""
    return client.get_account_positions()
```

With:
```python
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
```

- [ ] **Step 11: Update fetch_open_position_by_ticker**

Replace:
```python
@mcp.tool("fetch_open_position_by_ticker")
def fetch_open_position_by_ticker(ticker: str) -> Position:
    """Fetch a position by ticker (deprecated)."""
    return client.get_account_position_by_ticker(ticker)
```

With:
```python
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
```

- [ ] **Step 12: Update search_specific_position_by_ticker**

Replace:
```python
@mcp.tool("search_specific_position_by_ticker")
def search_position_by_ticker(ticker: str) -> Position:
    """Search for a position by ticker using POST endpoint."""
    return client.search_position_by_ticker(ticker)
```

With:
```python
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
```

- [ ] **Step 13: Update fetch_historical_order_data**

Replace:
```python
@mcp.tool("fetch_historical_order_data")
def fetch_historical_order_data(
    cursor: int = None, ticker: str = None, limit: int = 20
) -> list[HistoricalOrder]:
    """Fetch historical order data with pagination."""
    return client.get_historical_order_data(cursor=cursor, ticker=ticker, limit=limit)
```

With:
```python
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
```

- [ ] **Step 14: Update fetch_paid_out_dividends**

Replace:
```python
@mcp.tool("fetch_paid_out_dividends")
def fetch_paid_out_dividends(
    cursor: int = None, ticker: str = None, limit: int = 20
) -> PaginatedResponseHistoryDividendItem:
    """Fetch historical dividend data with pagination."""
    return client.get_dividends(cursor=cursor, ticker=ticker, limit=limit)
```

With:
```python
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
```

- [ ] **Step 15: Update fetch_exports_list**

Replace:
```python
@mcp.tool("fetch_exports_list")
def fetch_exports_list() -> list[ReportResponse]:
    """Lists detailed information about all csv account exports."""
    return client.get_reports()
```

With:
```python
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
```

- [ ] **Step 16: Update fetch_transaction_list**

Replace:
```python
@mcp.tool("fetch_transaction_list")
def fetch_transaction_list(
    cursor: str | None = None, time: str | None = None, limit: int = 20
) -> PaginatedResponseHistoryTransactionItem:
    """Fetch superficial information about movements to and from your
    account."""
    return client.get_history_transactions(cursor=cursor, time_from=time, limit=limit)
```

With:
```python
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
```

- [ ] **Step 17: Run all existing tests to catch regressions**

```bash
uv run pytest tests/ -v
```

Expected: all tests PASS (accounts and response tests; tools aren't unit-tested yet).

- [ ] **Step 18: Commit**

```bash
git add src/tools.py
git commit -m "feat: add optional account param to all read tools"
```

---

## Task 6: Update write tools

**Files:**
- Modify: `src/tools.py`

Write tools are: `create_pie`, `delete_pie`, `update_pie`, `duplicate_pie`, `place_limit_order`, `place_market_order`, `place_stop_order`, `place_stop_limit_order`, `cancel_order`, `request_csv_export`.

- [ ] **Step 1: Update create_pie**

Replace:
```python
@mcp.tool("create_pie")
def create_pie(
    name: str,
    instrument_shares: dict[str, float],
    dividend_cash_action: Optional[DividendCashActionEnum] = None,
    end_date: Optional[datetime] = None,
    goal: Optional[float] = None,
    icon: Optional[str] = None,
) -> AccountBucketInstrumentsDetailedResponse:
```

With:
```python
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
```

- [ ] **Step 2: Update delete_pie**

Replace:
```python
@mcp.tool("delete_pie")
def delete_pie(pie_id: int):
    """Delete a pie."""
    return client.delete_pie(pie_id)
```

With:
```python
@mcp.tool("delete_pie")
def delete_pie(pie_id: int, account: str):
    """
    Delete a pie.

    Args:
        pie_id: ID of the pie to delete
        account: Account name that owns the pie (required)
    """
    return registry.get_client(account).delete_pie(pie_id)
```

- [ ] **Step 3: Update update_pie**

Replace:
```python
@mcp.tool("update_pie")
def update_pie(
    pie_id: int,
    name: str = None,
    instrument_shares: dict[str, float] = None,
    dividend_cash_action: Optional[DividendCashActionEnum] = None,
    end_date: Optional[datetime] = None,
    goal: Optional[float] = None,
    icon: Optional[str] = None,
) -> AccountBucketInstrumentsDetailedResponse:
```

With:
```python
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
```

- [ ] **Step 4: Update duplicate_pie**

Replace:
```python
@mcp.tool("duplicate_pie")
def duplicate_pie(
    pie_id: int, name: Optional[str] = None, icon: Optional[str] = None
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
    duplicate_request = DuplicateBucketRequest(name=name, icon=icon)
    return client.duplicate_pie(pie_id, duplicate_request)
```

With:
```python
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
```

- [ ] **Step 5: Update place_limit_order**

Replace:
```python
@mcp.tool("place_limit_order")
def place_limit_order(
    ticker: str,
    quantity: float,
    limit_price: float,
    time_validity: LimitRequestTimeValidityEnum = LimitRequestTimeValidityEnum.DAY,
) -> Order:
```

With:
```python
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
```

- [ ] **Step 6: Update place_market_order**

Replace:
```python
@mcp.tool("place_market_order")
def place_market_order(ticker: str, quantity: float) -> Order:
    """
    Place a market order to buy or sell an instrument at the current market price.

    Args:
        ticker: Ticker symbol of the instrument to trade (e.g., 'AAPL_US_EQ')
        quantity: Number of shares/units to trade

    Returns:
        Order: Details of the placed order
    """
    market_request = MarketRequest(ticker=ticker, quantity=quantity)
    return client.place_market_order(market_request)
```

With:
```python
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
```

- [ ] **Step 7: Update place_stop_order**

Replace:
```python
@mcp.tool("place_stop_order")
def place_stop_order(
    ticker: str,
    quantity: float,
    stop_price: float,
    time_validity: StopRequestTimeValidityEnum = StopRequestTimeValidityEnum.DAY,
) -> Order:
```

With:
```python
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
```

- [ ] **Step 8: Update place_stop_limit_order**

Replace:
```python
@mcp.tool("place_stop_limit_order")
def place_stop_limit_order(
    ticker: str,
    quantity: float,
    stop_price: float,
    limit_price: float,
    time_validity: StopLimitRequestTimeValidityEnum = StopLimitRequestTimeValidityEnum.DAY,
) -> Order:
```

With:
```python
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
```

- [ ] **Step 9: Update cancel_order**

Replace:
```python
@mcp.tool("cancel_order")
def cancel_order_by_id(order_id: int) -> None:
    """Cancel an existing order."""
    return client.cancel_order(order_id)
```

With:
```python
@mcp.tool("cancel_order")
def cancel_order_by_id(order_id: int, account: str) -> None:
    """
    Cancel an existing order.

    Args:
        order_id: ID of the order to cancel
        account: Account name that owns the order (required)
    """
    return registry.get_client(account).cancel_order(order_id)
```

- [ ] **Step 10: Update request_csv_export**

Replace the function signature and body:
```python
@mcp.tool("request_csv_export")
def request_csv_export(
    include_dividends: bool = True,
    include_interest: bool = True,
    include_orders: bool = True,
    include_transactions: bool = True,
    time_from: str = None,
    time_to: str = None,
) -> EnqueuedReportResponse:
```

With:
```python
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
```

- [ ] **Step 11: Run all tests**

```bash
uv run pytest tests/ -v
```

Expected: all tests PASS.

- [ ] **Step 12: Commit**

```bash
git add src/tools.py
git commit -m "feat: add required account param to all write tools"
```

---

## Task 7: Add list_accounts tool

**Files:**
- Modify: `src/tools.py`

- [ ] **Step 1: Add list_accounts at the top of the tools section in src/tools.py**

Add this function immediately after the imports in `src/tools.py`:

```python
@mcp.tool("list_accounts")
def list_accounts() -> dict:
    """
    List all configured Trading212 accounts and the default account name.

    Returns:
        dict with 'default' (str) and 'accounts' (list of str) keys
    """
    return {
        "default": registry.default_name(),
        "accounts": registry.account_names(),
    }
```

- [ ] **Step 2: Run all tests**

```bash
uv run pytest tests/ -v
```

Expected: all tests PASS.

- [ ] **Step 3: Commit**

```bash
git add src/tools.py
git commit -m "feat: add list_accounts tool to expose configured account names"
```

---

## Task 8: Create accounts.json.example

**Files:**
- Create: `accounts.json.example`

- [ ] **Step 1: Create the example config file**

Create `accounts.json.example` at the repo root:

```json
{
  "default": "my_account",
  "accounts": [
    {
      "name": "my_account",
      "api_key": "YOUR_API_KEY_HERE",
      "api_secret": "YOUR_API_SECRET_HERE",
      "environment": "live"
    },
    {
      "name": "demo_account",
      "api_key": "YOUR_DEMO_API_KEY_HERE",
      "api_secret": "YOUR_DEMO_API_SECRET_HERE",
      "environment": "demo"
    }
  ]
}
```

- [ ] **Step 2: Add accounts.json to .gitignore**

Append to `.gitignore` (create it if it doesn't exist):

```
accounts.json
```

- [ ] **Step 3: Commit**

```bash
git add accounts.json.example .gitignore
git commit -m "chore: add accounts.json.example template and gitignore real config"
```

---

## Task 9: Full regression test

**Files:** None (verification only)

- [ ] **Step 1: Run all tests**

```bash
uv run pytest tests/ -v
```

Expected: all tests PASS with no warnings about missing imports.

- [ ] **Step 2: Verify server starts cleanly with backward-compat env vars**

With no `accounts.json` present (rename it if it exists) and env vars set:

```bash
TRADING212_API_KEY=testkey TRADING212_API_SECRET=testsecret ENVIRONMENT=demo \
  uv run python -c "
import sys; sys.path.insert(0, 'src')
from accounts import AccountRegistry
r = AccountRegistry(config_path='/tmp/nonexistent.json')
print('default:', r.default_name())
print('accounts:', r.account_names())
print('resolve(None):', list(r.resolve(None).keys()))
"
```

Expected output:
```
default: default
accounts: ['default']
resolve(None): ['default']
```

- [ ] **Step 3: Verify error message on unknown account**

```bash
uv run python -c "
import sys, json, tempfile, os
sys.path.insert(0, 'src')
cfg = {'default': 'sumeet', 'accounts': [{'name': 'sumeet', 'api_key': 'k', 'api_secret': 's', 'environment': 'demo'}]}
with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
    json.dump(cfg, f); path = f.name
from accounts import AccountRegistry
r = AccountRegistry(config_path=path)
os.unlink(path)
try:
    r.get_client('wife')
except ValueError as e:
    print('Error:', e)
"
```

Expected output:
```
Error: Account 'wife' not found. Available accounts: sumeet
```

- [ ] **Step 4: Final commit**

```bash
git add -A
git commit -m "chore: verified multi-account implementation complete"
```
