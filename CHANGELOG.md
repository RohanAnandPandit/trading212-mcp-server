# Changelog

## 0.2.0 — Unreleased

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
