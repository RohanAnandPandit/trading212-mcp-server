# Changelog

## 0.2.0 — Unreleased

- Package the repository as a Claude Code plugin and marketplace: the `trading212` plugin bundles the server and the portfolio analysis skill, prompts for credentials (stored in secure storage) and the demo/live environment, and caches responses in the plugin data directory.
- Add the free Trading 212 Portfolio Analysis skill (read-only account analysis) with a reproducible Agensi packaging script.
- Add an optional `next_page_path` argument to the history tools so the next page can be fetched by passing `nextPagePath` back unchanged.
- Report Trading 212's short error `code` (for example an order rejection reason) in failed-request errors, never other upstream text.
- Cap `search_instrument` results with a `limit` argument (default 100) and rank exact ticker, symbol or name matches first.
- Mark `create_pie`, `duplicate_pie` and `request_csv_export` as non-destructive; note in pie tool descriptions that the endpoints are deprecated upstream.
- Add `TRADING212_HOST` (loopback only) and `TRADING212_PORT` for the HTTP transports.
- Update to MCP SDK 2.3, pydantic 2.14.3 and filelock 4.2.11.
- Keep unknown upstream enum values in responses as strings instead of rejecting the whole response; request enums stay strict.
- Stop requiring exchange, working-schedule, and time-event fields that the public schema leaves optional.
- Preserve tax charge dates and currencies; tolerate additional nested export response fields.
- Validate endpoint responses before caching and test model coverage against the API snapshot.
- Separate security auditing from quality checks; add a dependency lock/export update helper.

- Migrate to MCP SDK 2.x and current supported dependencies; add a typed installable package.
- Preserve 28 tools, 16 resource registrations, the prompt, and the script launcher.
- Create API clients during server lifespan and close them on shutdown.
- Replace legacy file caching with credential-free SQLite caching and cross-process invalidation.
- Add category TTLs, freshness metadata, bounded GET retries, request validation, and safe errors.
- Harden local HTTP transport and non-root Docker builds; exclude local secrets and caches.
- Add offline endpoint, protocol, package, and concurrency tests, static checks and dependency auditing.
- Refresh the Trading 212 schema snapshot and accept newly documented transaction and order-origin values.

Migration: install the new lockfile and rebuild Docker images. Legacy cache paths
are ignored and remain for explicit user cleanup. Some previously accepted invalid
requests now fail validation. Package version does not imply a published release.
