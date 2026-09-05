# Modernization review and validation

Reviewed on 2026-09-04. Version 0.2.0 is prepared in the source tree; no package
publication, deployment, or live Trading 212 calls form part of this work.

## Delivered changes

1. **Regression coverage and security:** captured the original MCP discovery
   surface and model fields; added offline endpoint, protocol, invalid-input,
   authentication, credential-storage, and concurrency checks. HTTP Host/Origin
   rejection and protocol-clean stdio are verified.
2. **Packaging and lifecycle:** installable `trading212_mcp` package, console and
   module entry points, compatibility script, explicit domain modules, validated
   settings, and server-owned client lifetime. Static resources use a provider
   owned by the server rather than SDK Context injection.
3. **Dependencies and cache:** MCP 2.1.1, Hishel 1.3.1, Pydantic 2.13.5,
   python-dotenv 1.2.3, HTTPX 0.28.1, and pytest 9.1.1. Refreshed transitive
   dependencies, generated hash-pinned requirements, credential-free SQLite
   storage, category TTLs, cross-process locking and mutation invalidation.
4. **Maintenance:** Ruff, strict mypy, coverage reporting, dependency audit,
   Python/platform CI matrix, wheel/container checks, pinned actions and container
   bases, Dependabot, and corrected setup/security documentation.

## Compatibility

The 28 tool names, 11 static resources, five resource templates, and analysis
prompt remain. Model fields and requiredness are checked against captured
snapshots. Tool arguments retain their names and documented optionality.
Nullability and order validation are corrected.
Response payload fields are preserved; freshness is added through MCP `_meta`.
Old internal Python import paths are replaced by the installed package; the
supported `src/server.py` launch path remains.

## Verification

- 96 offline tests pass; Python 3.11 coverage is 96% including branch coverage.
- Supported interpreter matrix: Python 3.11, 3.12, 3.13, and stable 3.14.
- Ruff checks, formatting checks, strict mypy, and whitespace checks pass.
- Source distribution and wheel build successfully; an installed wheel outside
  the checkout completes MCP discovery without an editable source dependency.
- Docker build and offline stdio discovery pass. The image runs as UID 10001;
  synthetic environment/cache files in the build context are excluded.
- Dependency audit of the refreshed environment reports **zero known
  vulnerabilities**, with 79 dependency records and no skipped records. The
  initial audit found eight advisories across Click, Pygments, and
  python-multipart; their locked upgrades resolved those findings. No advisory
  suppressions or allowlists were added.
- Hosted CI passes on Linux with Python 3.11–3.14 and on Windows and macOS with
  Python 3.11; the quality and Linux container jobs also pass.

The audit is a point-in-time dependency database check, not a claim that all
possible security vulnerabilities have been eliminated. CI produces an updated
machine-readable audit artifact on each run.

## Operational boundaries

Caches still contain private financial responses in plaintext. Credentials and
cookies are excluded. Filesystem protections and file locks assume a private local
disk; shared/network filesystems are unsupported. Old cache directories are ignored
and preserved for explicit cleanup. Mutations outside this credential namespace
are observed after the configured TTL, not instantaneously.

GET retries are limited to two within a 30-second scheduling budget, with explicit
HTTP phase timeouts. Lock acquisition is bounded separately. HTTPX timeouts are
per operation, not a hard wall-clock cancellation of a peer that continuously
streams data. Mutations are never automatically retried; uncertain outcomes
invalidate private caches and return an error. No new remote access or
multi-user service is introduced.
