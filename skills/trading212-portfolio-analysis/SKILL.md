---
name: trading212-portfolio-analysis
description: Connect the Trading 212 MCP server and summarize portfolio holdings, cash, open orders, dividends and transaction history. Use when the user asks to set up Trading 212, review their T212 portfolio, inspect positions or summarize account history. Does not execute trades, change pies or request exports.
---

# Trading 212 Portfolio Analysis

Use the user's locally connected `trading212-mcp-server` to answer account-data
questions. Fetch only the data needed for the request. This skill provides
descriptive analysis, not investment recommendations or independent market feeds.

## Connection and setup

For setup, follow the repository's single canonical
[README setup process](https://github.com/RohanAnandPandit/trading212-mcp-server/blob/main/README.md#setup).
Reuse an existing checkout without overwriting local changes. Default new setups
to `ENVIRONMENT=demo` and `TRANSPORT=stdio`; do not switch an existing account's
environment without the user's choice. Confirm workspace or global configuration
scope before saving client settings.

The user enters credentials locally into the server's ignored `.env`. Never
request credentials in chat, read that file, inspect secret environment values,
or put credentials in commands, logs or client configuration. If credentials
are missing, pause for local entry. Do not repeatedly call account tools.

Verify setup using MCP tool discovery only. Listing tools, resources and prompts
does not call Trading 212. Reading account resources or retrieving the
`analyse_trading212_data` prompt can call the account API, so neither is a setup
check. Report where configuration was saved and whether discovery succeeded.
If tools are unavailable, explain the missing connection and offer setup; never
substitute invented account data. Agensi delivers the instructions; the local
Trading 212 server must be connected separately to the same capable agent.

## Read and interpret account data

1. Establish the requested question and period. Identify demo/live from known
   non-secret client configuration or ask the user; do not infer it from balances
   or assume that a connected server uses demo. Label it unknown if unconfirmed.
2. Use discovered tool schemas and names. Prefer `fetch_account_summary` for
   account currency and aggregate values; `fetch_positions` for holdings;
   `fetch_all_orders` for open orders; `fetch_paid_out_dividends`,
   `fetch_transaction_list` and `fetch_historical_order_data` for history.
   Use `fetch_account_cash` only when a separate cash query is useful.
3. Prefer supplied account-currency totals and `walletImpact` values. Instrument
   prices may be in another currency. Convert GBX to GBP by dividing by 100 only
   when the source unit is confirmed. Never sum unlike currencies or invent an
   FX rate. Missing values are unavailable, not zero. Distinguish unrealized
   profit/loss from realized profit/loss and cash flows from investment returns.
4. Historical tools return one page. To continue, call the same tool again with
   only `next_page_path` set to the returned `nextPagePath`, unchanged; a null
   value means no more pages. If the discovered schema has no `next_page_path`
   (older servers), pass the path's supported cursor/query arguments instead.
   Do not fetch that URL directly. Continue only as needed for the requested
   period, respecting rate limits; stop on repeated cursors or errors and disclose
   incomplete coverage. Never describe a page subtotal as a full-period total.
5. Inspect freshness metadata under
   `_meta["io.github.RohanAnandPandit.trading212/cache"]` when present:
   `cacheHit`, `retrievedAt` and `ttlSeconds`. Report the retrieval time and
   cached status; do not describe cached values as live. If freshness metadata
   is missing, say freshness is unavailable. Do not alter cache settings or
   repeatedly poll to force a refresh.

Present a concise answer followed by the relevant figures, with currency units,
environment, requested/observed period and freshness. State material missing
fields, partial results and calculation assumptions. Only calculate allocation
percentages when values share a confirmed currency and the denominator is known;
label whether the denominator is holdings or the whole account. Successful empty
results mean no returned records, while failed retrieval means unknown data.

For detailed mappings, pagination and synthetic examples, read
[the analysis guide](references/analysis-guide.md) if available. The rules above
are sufficient when the distribution channel cannot supply supporting files.

## Boundaries

Do not place or cancel orders, create/update/duplicate/delete pies, request CSV
exports, follow export download links, change API permissions or expose the local
server publicly. If asked for a mutation, explain that it falls outside this
analysis skill and do not invoke a write tool, even if the user authorizes it.
This restriction applies to this skill's workflow, not unrelated user work.

These instructions do not remove or disable server tools. Recommend read-only
API permissions where available and client approval controls for mutations.
Do not send account data to Agensi, telemetry endpoints or other services.
Use only the user's chosen MCP server for account requests. Report API errors
without echoing credentials, raw private diagnostics or account identifiers.

Independently maintained; not affiliated with or endorsed by Trading 212.
