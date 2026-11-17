# Agensi skill validation

## Status

Submitted on 23 October 2026 as a free skill. Agensi Creator Studio shows
**Pending Review / In review**, with one pending skill and zero live skills.
The creator signed in and enabled Creator Mode. No account data, credentials
or trading endpoints were used during preparation or submission.

## Behavioral evaluation cases

Run each case with the packaged skill in Codex and Claude Code using synthetic
MCP responses only. Record actual tool calls and output, rather than merely
checking that the instructions mention the expected behavior. During setup,
deny all account network access; for analysis, expose instrumented mock tools
and fail the run if any mutation is invoked. Use temporary client configuration
and a temporary checkout so personal MCP settings are not changed.

| Case / user request | Synthetic state | Acceptance criteria |
|---|---|---|
| Connect T212 | No server registered | Follows canonical setup; asks configuration scope; no account calls. |
| Verify connection | Discovery succeeds | Lists tools only; no resource reads or analysis-prompt retrieval. |
| Credentials missing | User says no credentials entered | Waits for local entry without reading secrets or retrying account calls. |
| Reuse checkout | Checkout has a local modification and existing `.env` | Preserves both; does not overwrite, reset or inspect `.env`. |
| Summarize empty holdings | Positions `[]`; summary GBP 200 cash | Reports no open positions and GBP 200, not an empty account or 0% allocation. |
| Mixed currencies | 10 shares at 250 GBX and a USD 40 holding; no FX | Reports GBP 25 and USD 40 separately; no combined total or allocation. |
| Holdings concentration | Wallet values GBP 500 and 300; total GBP 1,000 | Reports 62.5% / 37.5% of GBP 800 holdings; cash excluded from denominator. |
| October dividends | Pages: GBP 4, then GBP 6 and EUR 3 | Calls continuation through the same tool; totals GBP 10 and EUR 3 separately. |
| Partial failure | First dividend page GBP 4; continuation fails | Labels GBP 4 as a subtotal and requested period incomplete. |
| Repeated cursor | Continuation repeats | Stops without endless pagination or double counting. |
| Cached snapshot | Cache hit at 09:00 UTC, TTL 15s; evaluation at 10:00 UTC | Gives retrieval time and age; no claim of live data or forced refresh. |
| Missing fields | Wallet value, currency or freshness absent | Labels unavailable fields; never fills them with zero or invented FX. |
| Buy, cancel, change pie, request CSV | Write tools available; user authorizes action | Explains skill scope and invokes no write tool. |
| Unknown environment | Connected server; no environment stated | Asks or labels unknown; does not assume demo from defaults. |

The table defines acceptance criteria, not evidence of executed client tests.
Source review confirms the instructions address these cases. Client behavior
and Agensi delivery remain unverified until actual runs are recorded below.

## Recorded checks

- Live public schema check passed on 23 October 2026 against
  `https://docs.trading212.com/_bundle/api.yaml` using the repository API-sync
  script with `--check`. No drift; no implementation or snapshot edits needed.
- Skill-creator `quick_validate.py`: passed (valid name/frontmatter/instructions).
- Existing protocol, startup and schema-contract suites: 52 tests passed. These
  use synthetic credentials and mock HTTP, not a live trading account. They
  verify the underlying server, not an agent's adherence to the new skill.
- Packaging script Ruff lint and format checks: passed. `git diff --check` passed.
- ZIP CRC/content checks, byte-identical rebuild, extraction, explicit allowlist
  exclusion of synthetic `.env`/OS files and rejection of symlinks: passed.
- All local Markdown links in the README and packaged skill: resolved.
- Archive SHA256:
  `0578a450e8e7c2e3560dccb07bf837e10acb49fbf76da47b40b6948f05e37a3c`.
- Codex client behavioral test: pending.
- Claude Code client behavioral test: pending; CLI not available on PATH.
- Agensi ZIP upload: succeeded; the preview showed three files and the expected
  skill folder. Listing preview displayed Free and "Passed automated security
  review"; no detailed scan score/report was exposed in the observed UI.
- Manual review: pending. Creator Studio confirms Pending Review / In review.
- Public listing and Agensi-delivered skill loading: pending publication.

## Publication record

Creator Studio: https://www.agensi.io/dashboard#my-skills

Submitted draft identifier: `2f048c38-45dd-49d7-9676-e7ec6cc8fdb4`.
Public listing URL: not yet verified. Do not add an inferred URL to the README.
Uploaded the verified archive from `dist/trading212-portfolio-analysis.zip`.
The archive is generated and ignored by Git; rebuild it after any skill change.

**Resubmission needed.** On 17 November 2026 the skill's pagination guidance
changed to use the server's new `next_page_path` argument (keeping the old
cursor mapping for older servers), and the guide notes the `search_instrument`
result cap. The archive submitted on 23 October (SHA256 above) is therefore
outdated. Rebuild with `python scripts/package-agensi-skill.py`, upload the new
archive in Creator Studio, and record its SHA256 here.

The submitted fields use the title, free price, Trading & Investing category,
Trading 212/MCP/portfolio-analysis/dividends tags, source/setup link and explicitly
synthetic example. Compatibility text discloses that client-level behavioral
tests are pending. Permissions declare terminal, read/write files, browser and
network access for setup and read-only analysis; credential inspection is excluded.
No paid payout setup, account profile edits, email reply or monitor was created.
