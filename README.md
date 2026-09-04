# Trading 212 MCP Server

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Checks](https://github.com/RohanAnandPandit/trading212-mcp-server/actions/workflows/tests.yml/badge.svg)](https://github.com/RohanAnandPandit/trading212-mcp-server/actions/workflows/tests.yml)

A [Model Context Protocol](https://modelcontextprotocol.io/) server
for the [Trading 212 public API](https://docs.trading212.com/api). It exposes
account data, positions, orders, pies, instrument metadata, and account history.
It also includes an account-currency-aware analysis prompt. It does not provide
independent market feeds, investment recommendations, or real-time streaming.

Python 3.11–3.14 is supported. The current source package version is 0.2.0;
see [the changelog](CHANGELOG.md) for upgrade details. The project uses the
official MCP Python SDK 2.x.

## Install and run

Install [uv](https://docs.astral.sh/uv/getting-started/installation/), then:

```sh
git clone https://github.com/RohanAnandPandit/trading212-mcp-server.git
cd trading212-mcp-server
uv sync --frozen
cp .env.example .env
# Edit .env with your own credentials.
uv run --frozen trading212-mcp-server
```

Alternatively, install the package from the checkout using `pip install .`,
then run `trading212-mcp-server`. For a locked pip installation, use
`pip install --require-hashes -r requirements.txt` followed by
`pip install --no-deps .`.

Generate credentials in your Trading 212 account's API settings. Set
`TRADING212_API_KEY` and, for Basic authentication, `TRADING212_API_SECRET`.
API-key-only authentication remains available for existing integrations, where
accepted by Trading 212. Use the demo environment for testing. Live credentials
and `ENVIRONMENT=live` enable operations on the real account.

The server reads `.env` in its working directory at startup. Existing process
environment variables take precedence. Imports and tool discovery do not make
Trading 212 requests. No credentials are required merely to import the server.

### Desktop MCP configuration

Use this configuration in your MCP client's server settings:

```json
{
  "mcpServers": {
    "trading212": {
      "command": "uv",
      "args": ["run", "--frozen", "--directory", "/absolute/path/to/trading212-mcp-server", "trading212-mcp-server"],
      "env": {
        "TRADING212_API_KEY": "YOUR_API_KEY",
        "TRADING212_API_SECRET": "YOUR_API_SECRET",
        "ENVIRONMENT": "demo"
      }
    }
  }
}
```

Existing configurations pointing to `src/server.py` continue to work after
`uv sync --frozen`. The script also remains the Inspector entry point:

```sh
uv run --frozen mcp dev src/server.py
```

Inspector requires Node.js and `npx`. Tool calls in Inspector use the configured
account, including mutations when you invoke those tools.

### Docker

```sh
docker build -t trading212-mcp-server .
docker run --rm -i --env-file .env trading212-mcp-server
```

For a desktop client, pass both credential variables through Docker:

```json
{
  "mcpServers": {
    "trading212": {
      "command": "docker",
      "args": ["run", "--rm", "-i", "-e", "TRADING212_API_KEY", "-e", "TRADING212_API_SECRET", "-e", "ENVIRONMENT", "trading212-mcp-server"],
      "env": {
        "TRADING212_API_KEY": "YOUR_API_KEY",
        "TRADING212_API_SECRET": "YOUR_API_SECRET",
        "ENVIRONMENT": "demo"
      }
    }
  }
}
```

The image runs as UID/GID 10001. Credentials, local caches, and development
files are excluded from the image. The default container cache is ephemeral;
mount a private directory writable by UID 10001 at `/home/app/.cache` if you
want persistence. Stdio does not require publishing a port.

## Configuration

| Variable | Default | Meaning |
|---|---|---|
| `TRADING212_API_KEY` | Required | Account API key |
| `TRADING212_API_SECRET` | Unset | Secret for Basic authentication |
| `ENVIRONMENT` | `demo` | `demo` or `live` |
| `TRANSPORT` | `stdio` | `stdio`, `sse`, or `streamable-http` |
| `TRADING212_CACHE_DIR` | `.cache/trading212-v3` | Cache root; relative to working directory |
| `TRADING212_ACCOUNT_TTL` | `15` | Account, positions, orders, pies, export-status cache seconds |
| `TRADING212_HISTORY_TTL` | `300` | History cache seconds |
| `TRADING212_METADATA_TTL` | `3600` | Instrument and exchange cache seconds |

A TTL of zero disables caching for that category. Values must be finite and
non-negative. HTTP transports bind only to `127.0.0.1:8000`, with explicit
Host/Origin restrictions. This is a local single-account server; hosted access,
public HTTP binding, and multi-user authentication are not provided. Do not
expose it through a public proxy or tunnel. Tool annotations describe effects;
they do not implement permissions. Use API permissions and your MCP client's
approval controls to govern account mutations.

## Tools

All previous tool names are retained:

| Area | Tools |
|---|---|
| Account | `fetch_account_summary`, `fetch_account_cash`, `fetch_account_info` |
| Positions | `fetch_positions`, `fetch_position_by_ticker`, `fetch_all_open_positions`, `fetch_open_position_by_ticker`, `search_specific_position_by_ticker` |
| Orders | `fetch_all_orders`, `fetch_order`, `place_market_order`, `place_limit_order`, `place_stop_order`, `place_stop_limit_order`, `cancel_order` |
| Pies | `fetch_pies`, `fetch_a_pie`, `create_pie`, `update_pie`, `duplicate_pie`, `delete_pie` |
| Metadata | `search_instrument`, `search_exchange` |
| History | `fetch_historical_order_data`, `fetch_paid_out_dividends`, `fetch_transaction_list`, `fetch_exports_list`, `request_csv_export` |

Positive order quantities buy; negative quantities sell. Zero/non-finite
quantities, non-positive prices, and empty tickers are rejected. Updating a pie
requires a non-empty name. Export dates must include a timezone and be ordered.
Pies are deprecated upstream, but their tools are retained.

`fetch_account_info` aliases `fetch_account_summary`. The older position tools
remain compatibility aliases. Historical tools return a single page with
`nextPagePath`; pass its cursor and other query parameters to fetch the next
page. Limits retain their existing clamp to 1–50. Requests do not automatically
traverse all pages or follow export download links.

## Resources and prompt

Resources retain their existing URIs:

- `trading212://account/summary`, `trading212://account/cash`
- `trading212://positions`, `trading212://positions/{ticker}`
- `trading212://orders`, `trading212://orders/{order_id}`
- `trading212://pies`, `trading212://pies/{pie_id}`
- `trading212://instruments`, `trading212://exchanges`
- `trading212://history/exports`

Compatibility URIs: `trading212://account/info`,
`trading212://account/portfolio`, `trading212://account/positions`,
`trading212://account/portfolio/{ticker}`, and
`trading212://account/positions/{ticker}`.

The `analyse_trading212_data` prompt includes account currency when available
and explains GBX/GBP units. If account retrieval fails, it still returns the
base prompt and writes a generic diagnostic to stderr.

## Cache and request guarantees

Private data remains cached. Credential/base-URL fingerprints isolate SQLite
storage across accounts, secret rotations, environments, and API versions.
Authorization and cookies never enter the cache layer. Cache responses contain
financial data in plaintext; private filesystem permissions are not encryption.
Use a private local disk, not a shared or network-mounted cache directory.

Only successful GETs are cached, and expired responses are never served.
Mutations are never cached or automatically retried. After any attempted
mutation, private-cache generations advance, including when the outcome is
uncertain. A cross-process file lock covers reads, writes, body consumption,
and invalidation, preventing older in-flight reads from repopulating the current
generation. Different credential namespaces remain independent; external trades
or writes using another API key may remain invisible until the TTL expires.

MCP tool results and resource contents carry freshness details under
`_meta["io.github.RohanAnandPandit.trading212/cache"]`: an array of `cacheHit`,
`retrievedAt` (UTC), and `ttlSeconds` records. Existing data fields remain intact.

Transient GET failures may be retried twice within a 30-second retry budget,
respecting `Retry-After` and rate-reset headers. Individual HTTP operations have
explicit timeouts. Waiting for another process's cache lock is bounded separately
at 30 seconds. A failed mutation can have an unknown outcome: check the account
before deciding whether to issue it again.

### Upgrading from 0.1.x

Stop older server processes, update the checkout, and run `uv sync --frozen`.
The new server never reads or migrates `.cache/hishel` or `.cache/trading212-v2`.
Those directories may contain private responses and Authorization headers.
After confirming the paths belong to this application, explicitly remove old
cache directories yourself. The upgrade does not delete user data. Rebuild
Docker images and replace any older images that may have included local files.

## Development and security

See [CONTRIBUTING.md](CONTRIBUTING.md) for architecture and verification commands,
[SECURITY.md](.github/SECURITY.md) for private reporting, and
[the modernization validation report](docs/modernization.md) for checked behavior.
`docs/api.json` is the checked-in upstream schema snapshot, not a guarantee that
the live API has not changed.

This project is independently maintained and is not affiliated with or endorsed by Trading 212.
Consult the provider's current documentation and terms. Licensed under [MIT](LICENSE).
