---
name: trading212-api-sync
description: Verify and update this repository against Trading 212's live public OpenAPI schema. Use for API-facing code, model, documentation, compatibility, release-readiness, or schema-drift work in trading212-mcp-server.
---

# Trading 212 API sync

Treat `https://docs.trading212.com/_bundle/api.yaml` as authoritative and
`docs/api.json` as its reviewable snapshot. A passing test suite against the
snapshot does not establish current upstream compatibility.

## Workflow

1. From the repository root, run:

   ```sh
   uv run --with PyYAML python .agents/skills/trading212-api-sync/scripts/sync_api_schema.py --check
   ```

2. If drift exists, inspect the reported paths, then refresh the snapshot with
   `--update`. Review the Git diff before changing implementation code.
3. Reconcile every relevant change across endpoint paths and methods,
   authentication, parameters, defaults and limits, request bodies, response
   fields, enums, pagination, deprecations, tests, and user documentation.
4. Keep request validation strong where it reflects documented or necessary
   trading safety, but do not invent format restrictions such as undocumented
   ticker character sets. Response models must tolerate additive fields, and
   changed upstream enums require explicit review so a new value cannot reject
   an otherwise valid response unnoticed.
5. Preserve existing MCP names and compatibility aliases unless a deliberate
   breaking change is requested and documented.
6. Run Ruff, formatting, strict mypy, the full pytest suite, package build and
   smoke tests, requirements export, dependency audit, and container smoke test
   when release readiness is in scope.

The schema workflow is documentation-only: never provide credentials, call an
account endpoint, or invoke a trading mutation. Report the source URL, check
date, detected drift, implementation impact, validation performed, and any
remaining uncertainty.
