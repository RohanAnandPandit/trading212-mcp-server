# Agensi listing draft

Submitted on 23 October 2026; pending Agensi review. See `validation.md` for the
submission record. The fields below remain the reusable listing source.

- Title: Trading 212 Portfolio Analysis
- Skill identifier: `trading212-portfolio-analysis`
- Price: Free ($0)
- Category: Trading & Investing
- Tags: Trading 212, T212, MCP, portfolio analysis, holdings, dividends
- Author: Rohan Pandit
- License: MIT
- Source: https://github.com/RohanAnandPandit/trading212-mcp-server
- Setup: https://github.com/RohanAnandPandit/trading212-mcp-server/blob/main/README.md#setup

## Short description

Connect your local Trading 212 MCP server and turn holdings, cash, open orders,
dividends and transaction history into clear account summaries.

## Description

Understand your Trading 212 account using your own agent and local MCP server.
This free companion skill guides setup, selects the relevant read tools and
explains the returned figures with their currencies, freshness and limitations.

Ask it to summarize your portfolio, inspect holdings concentration, review open
orders or summarize dividends and cash movements for a period. It distinguishes
GBP from GBX, keeps different currencies separate and flags incomplete history.

The skill requires a separately connected local Trading 212 MCP server. Agensi
delivers the skill instructions; it does not host your account connection.
New setups start in demo mode. You enter API credentials locally, outside chat.

This skill does not execute orders, change pies or request CSV exports. The server
still exposes mutation tools, so use suitable API permissions and client approval
controls. It provides descriptive account analysis without investment
recommendations, independent market feeds or real-time streaming.

Independently maintained and not affiliated with or endorsed by Trading 212.

## Requirements and compatibility

- An agent that can load SKILL.md instructions and connect a local stdio MCP server.
- Git, uv and Python 3.11–3.14 for the server's documented setup.
- A Trading 212 account with API access and permissions for the requested reads.
- Agensi's connector for loading the listed skill through Agensi.

No named client compatibility claim is ready for publication. Codex and Claude
Code still require client-level behavioral testing; do not select those badges
based solely on portable Markdown or the server's protocol smoke check.

## Example prompts

- Help me connect the Trading 212 MCP server in demo mode.
- Summarize my T212 holdings and cash, including data freshness.
- Show my largest holdings as a percentage of invested value.
- Summarize my paid dividends for October, keeping currencies separate.

## Sample output (synthetic)

Demo account snapshot, retrieved 23 October 2026 at 09:00 UTC (cached; TTL 15s).
Total value GBP 1,000; investments GBP 800; available cash GBP 200.
Holding A represents 62.5% of invested value and holding B 37.5%.
These figures exclude cash from the allocation denominator and do not establish
investment returns over a period.

## Submission procedure

1. Review `validation.md` and complete outstanding client checks.
2. Build with `python scripts/package-agensi-skill.py`. Upload the ZIP printed by
   the command; do not zip the repository or include this listing in the skill.
3. Sign in at https://www.agensi.io/dashboard/submit using the creator's account.
   Authentication/account creation is a user step. No paid payout setup is needed
   for this free listing unless the dashboard explicitly requires further action.
4. Set the fields above, inspect the scan result and resolve reported findings
   without weakening credential or mutation boundaries. Submit for review.
5. Record the actual listing URL and review status in `validation.md`. After
   approval, verify the public free price, source/setup links and skill loading
   through Agensi with the separately connected local server.
6. Only then add the verified public Agensi link to the repository README. Never
   treat upload or submission as proof that the listing is live.

Official packaging guidance: https://www.agensi.io/learn/skill-md-creator-checklist
Submission terms: https://www.agensi.io/terms
