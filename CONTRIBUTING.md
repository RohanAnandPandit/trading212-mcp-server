# Contributing

## Setup and checks

Use Python 3.11–3.14 and uv 0.12.9 or newer:

```sh
uv sync --frozen
uv run --frozen ruff check .
uv run --frozen ruff format --check .
uv run --frozen mypy
uv run --frozen pytest --cov --cov-report=term-missing
uv run --frozen pip-audit --local
uv build --no-build-isolation
```

Tests use synthetic credentials, temporary directories, and mock HTTP transports.
They do not need a Trading 212 account. Stdio smoke tests launch local subprocesses
and perform discovery only. Cross-process cache tests use spawned processes so
connections and locks are not inherited. CI tests every supported Python version,
plus Windows and macOS, package installation, and Docker startup.

Use `feature/`, `fix/`, `chore/`, `docs/`, or `refactor/` branches as appropriate;
do not use the `codex/` prefix in this repository.

## Architecture

`src/trading212_mcp/` is the installed package. `server.create_server()` registers
handlers without reading credentials or opening an API connection. Lifespan owns
a single client and closes it on shutdown. Each server gets its own client
provider; there is no module-global account client. This also supports static MCP
resources, for which the SDK does not support injected Context arguments.

- `settings.py`: validated environment configuration; dotenv only at startup.
- `client.py`: endpoint mapping, HTTP requests, bounded GET retries, safe errors.
- `cache.py`: Hishel adapter, credential isolation, private storage and generation locks.
- `models/`: response and request types, grouped by API domain.
- `tools/`: typed MCP handlers by domain; resources and prompts are separate modules.
- `registration.py`: consistent effect annotations and safe exception mapping.

The MCP SDK runs synchronous handlers on worker threads. Keep client methods
synchronous; use the server's lifetime and shared cache coordination rather than
adding untracked background tasks. Keep the compatibility `src/server.py` launcher.
Use explicit imports and type annotations. Ruff handles formatting and imports;
mypy checks the complete installed package in strict mode.

## Public contracts

Keep tool names, argument names, resource URIs, and response fields compatible.
`tests/fixtures/mcp_v1.json` captures the original discovery surface;
`model_fields_v1.json` captures model fields and requiredness. Tests compare
these contracts while permitting validation improvements and effect annotations.
Avoid rewriting compatibility snapshots just to make a test pass.

Response models tolerate extra upstream fields. Request models reject unknown
fields and non-finite values. Preserve negative quantities for sell orders.
The checked-in OpenAPI schema is a reference: verify upstream changes before
altering endpoint paths, types, or deprecation status. Do not add live trading
calls to automated tests.

## Cache invariants

Credentials are attached only by the live HTTP client. Hishel receives sanitized
requests and an allowlisted response header set; never pass Authorization,
Set-Cookie, or arbitrary request/response headers into storage. Namespaces hash
both the full outgoing authorization identity and API base URL.

Each client owns its storage connection and closes it. A per-namespace file lock
serializes complete requests across processes, including streamed body consumption.
Generation state is updated under that lock after mutations, even uncertain ones.
The metadata generation is stable; private data uses a monotonically increasing
generation. Old entries expire through Hishel cleanup. Do not replace this with
an unlocked in-memory generation, or release the lock before body consumption.
SQLite transaction context managers do not close their connections; use explicit
closing as well. Keep warnings as errors in tests.

Cache payloads contain private financial data, although credentials are excluded.
Use private local directories. No automatic deletion or migration of legacy caches.
Tests must cover credential/secret/environment/version isolation, persistence,
expiration, concurrency, mutation invalidation, and absent credential bytes.

## Dependency changes

`pyproject.toml` defines supported ranges and `uv.lock` pins resolutions. Upgrade
with `uv lock --upgrade` and `uv sync --frozen`, review the changes, then regenerate:

```sh
uv export --frozen --no-dev --no-emit-project --output-file requirements.txt
```

Do not edit generated requirements or independently pin transitive dependencies.
Do not admit prereleases without an explicit compatibility decision. Run the audit,
protocol tests, and packaging checks after upgrades; Hishel and MCP major updates
need behavior verification. CI actions are pinned to commits; Dependabot proposes
updates for uv, actions, and Docker.

## Reporting issues

Use GitHub issues for reproducible bugs with synthetic examples. Report security
issues privately using [.github/SECURITY.md](.github/SECURITY.md); never include
credentials or account data in public issues. Contributions use the MIT license.
