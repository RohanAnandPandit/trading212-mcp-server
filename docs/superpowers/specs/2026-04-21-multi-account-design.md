# Multi-Account Support Design

**Date:** 2026-04-21  
**Status:** Approved  

## Overview

Extend the Trading212 MCP server to support multiple independent Trading212 accounts (e.g., personal, spouse, child), each with their own API credentials. Read queries can target one account, a subset, or all accounts. Write operations always target a single explicitly named account. A configurable default account is used when no account is specified.

---

## 1. Configuration — `accounts.json`

A JSON file at the repo root defines all accounts. Its path can be overridden via the `ACCOUNTS_CONFIG` environment variable.

```json
{
  "default": "sumeet",
  "accounts": [
    {"name": "sumeet", "api_key": "...", "api_secret": "...", "environment": "live"},
    {"name": "wife",   "api_key": "...", "api_secret": "...", "environment": "live"},
    {"name": "son",    "api_key": "...", "api_secret": "...", "environment": "demo"}
  ]
}
```

**Fields:**
- `default` — account name used when no `account` param is provided in a tool call
- `accounts` — list of account definitions; each has:
  - `name` — unique identifier used in tool calls (case-sensitive)
  - `api_key` / `api_secret` — Trading212 API credentials
  - `environment` — `"live"` or `"demo"`

**Backward compatibility:** If `accounts.json` does not exist, the server falls back to the current single-account env vars (`TRADING212_API_KEY`, `TRADING212_API_SECRET`, `ENVIRONMENT`), behaving identically to today.

---

## 2. Account Registry — `src/accounts.py`

A new `AccountRegistry` class is the single source of truth for all clients. It is instantiated once at server startup.

```python
class AccountRegistry:
    def __init__(self, config_path: str): ...
    def get_client(self, name: str) -> Trading212Client: ...
    def get_clients(self, names: list[str]) -> dict[str, Trading212Client]: ...
    def all_clients(self) -> dict[str, Trading212Client]: ...
    def account_names(self) -> list[str]: ...
    def default_name(self) -> str: ...
```

- Loads `accounts.json` at construction time
- Creates and caches one `Trading212Client` per account (no re-instantiation per request)
- Raises `ValueError` with actionable message for unknown account names

### `resolve_clients` helper (in `src/mcp_server.py`)

```python
def resolve_clients(account: str | list[str] | None) -> dict[str, Trading212Client]:
    if account is None:
        return {registry.default_name(): registry.get_client(registry.default_name())}
    if account == "all":
        return registry.all_clients()
    if isinstance(account, list):
        return registry.get_clients(account)
    return {account: registry.get_client(account)}
```

All tools call `resolve_clients(account)` to get a `{name: client}` dict, then fan out their API calls.

---

## 3. Tool Signatures

### Read tools — optional `account` parameter

All read tools gain an optional `account: str | list[str] | None = None` parameter.

- `None` → default account
- `"sumeet"` → single named account
- `["sumeet", "wife"]` → subset of accounts
- `"all"` → every configured account

Example:
```python
@mcp.tool("fetch_account_cash")
def fetch_account_cash(account: str | list[str] | None = None):
    clients = resolve_clients(account)
    results = {name: client.get_account_cash() for name, client in clients.items()}
    return format_response(results)
```

### Write tools — required `account` parameter

All write tools gain a required `account: str` parameter (no default). This prevents accidental writes to the wrong account.

Example:
```python
@mcp.tool("place_market_order")
def place_market_order(ticker: str, quantity: float, account: str):
    client = registry.get_client(account)
    return client.place_market_order(MarketRequest(ticker=ticker, quantity=quantity))
```

### New tool: `list_accounts`

```python
@mcp.tool("list_accounts")
def list_accounts() -> dict:
    """List all configured account names and the default account."""
```

Returns `{"default": "sumeet", "accounts": ["sumeet", "wife", "son"]}`. Allows the LLM to discover available accounts without the user needing to know them.

---

## 4. Response Format — `src/utils/response.py`

A new `format_response(results: dict[str, Any])` helper determines the response shape:

**Single account result** — data returned directly, identical to today. No breaking change for existing single-account callers.

```json
{"blocked": 0.0, "free": 1250.50, "invested": 8400.00, ...}
```

**Multiple account results** — grouped by account name:

```json
[
  {"account": "sumeet", "data": {"free": 1250.50, "invested": 8400.00}},
  {"account": "wife",   "data": {"free": 340.00,  "invested": 2100.00}}
]
```

**Aggregate-capable responses** (cash, portfolio value) — grouped results plus a `totals` entry that sums numeric fields across all accounts:

```json
[
  {"account": "sumeet", "data": {"free": 1250.50, "invested": 8400.00}},
  {"account": "wife",   "data": {"free": 340.00,  "invested": 2100.00}},
  {"account": "__totals__", "data": {"free": 1590.50, "invested": 10500.00}}
]
```

Aggregate totals apply to: `fetch_account_cash`. Totals for `fetch_all_open_positions` would require domain-specific aggregation (summing `quantity * currentPrice` across positions) and are out of scope for v1 — users can compute them client-side from the grouped response.

---

## 5. Error Handling

| Scenario | Behaviour |
|---|---|
| Unknown account name in any tool | `ValueError: "Account 'xyz' not found. Available accounts: sumeet, wife, son"` — raised before any API call |
| `accounts.json` missing + no legacy env vars | Server exits at startup: `"No accounts configured. Create accounts.json or set TRADING212_API_KEY."` |
| One account fails during multi-account read | Other accounts' results returned normally; failed account appears as `{"account": "wife", "error": "..."}` — partial failure does not abort the query |
| Write op with unknown account | Same `ValueError` as above |

---

## 6. Files Changed

| File | Change |
|---|---|
| `accounts.json` (new) | Account configuration file |
| `src/accounts.py` (new) | `AccountRegistry` class |
| `src/utils/response.py` (new) | `format_response` helper |
| `src/mcp_server.py` | Replace single `client` with `registry`; add `resolve_clients` helper |
| `src/tools.py` | Add `account` param to all tools; add `list_accounts` tool |
| `src/config.py` | Add `ACCOUNTS_CONFIG` env var support |

---

## 7. Out of Scope

- Cross-account write operations (e.g., same order on all accounts simultaneously)
- Account groups or tags beyond the flat name-based lookup
- UI for managing accounts (config file is the interface)
- Encryption of credentials in `accounts.json` (user responsibility; treat like `.env`)
