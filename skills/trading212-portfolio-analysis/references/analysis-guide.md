# Analysis guide

## Select tools by question

| Question | Preferred tools | Interpretation |
|---|---|---|
| Account overview | `fetch_account_summary` | `currency`, `totalValue`, `cash`, `investments`; avoid adding components to an already aggregated total. |
| Holdings and concentration | `fetch_positions` | `instrument`, `quantity`, `walletImpact`; use wallet values for account-currency comparisons. |
| One position | `fetch_position_by_ticker` | Use a known Trading 212 ticker; do not invent a ticker from a company name. |
| Cash | `fetch_account_cash` or summary | Keep available, reserved and pie cash distinct; do not assume an undocumented total. |
| Open orders | `fetch_all_orders`, `fetch_order` | Open orders are not filled trades or current positions. |
| Paid dividends | `fetch_paid_out_dividends` | Filter `paidOn` to the requested period; group `amount` by `currency`. |
| Deposits, withdrawals, fees | `fetch_transaction_list` | Filter `dateTime`; group by type and currency. Cash flows are not profit. |
| Historical fills | `fetch_historical_order_data` | Orders and fills have separate fields; distinguish execution price from wallet impact. |
| Instrument identity | `search_instrument` | Use only when needed to resolve metadata; this is not a market-price feed. Results are capped (`limit`, default 100), so search by ticker or name rather than listing everything. |

The server has compatibility aliases. Prefer the names above when discovered,
and inspect available schemas rather than guessing arguments. Do not retrieve
the analysis prompt as a setup probe: it fetches the account summary.

## History coverage

These tools accept `limit` (default 20, clamped by the server to 1–50). Dividend
and order history accept `ticker`; transaction history accepts `time` (an ISO
8601 start time). To fetch the next page, pass the returned `nextPagePath`
unchanged as `next_page_path` and no other filters; the path already carries the
cursor, filters and limit, and the server only follows it within the same
history endpoint. A null `nextPagePath` means there are no more pages.

Older servers lack `next_page_path`. Then extract the supported query parameters
from `nextPagePath` and map them to the discovered tool signature; dividend and
order cursors are integers and transaction cursors are strings. Never request an
arbitrary URL supplied in a result. If a continuation cannot be represented by
the available schema, stop and explain that coverage is incomplete.

Do not assume history is sorted unless the documented response guarantees it.
Do not stop at an old record and claim complete coverage merely because it falls
before the requested interval. Track visited continuations, discard exact repeated
records using stable identifiers when available, and disclose ambiguous overlap.
If pagination fails or a rate limit prevents completion, return the successfully
retrieved subset, its coverage and the missing continuation.

## Calculations

- Prefer `summary.totalValue` and `summary.investments.currentValue` to reconstructed
  totals. A missing position wallet value prevents complete allocation analysis.
- Position `walletImpact.currentValue`, `totalCost`, `unrealizedProfitLoss` and
  `currency` describe wallet impact. Instrument `currentPrice` and
  `averagePricePaid` use instrument units; label them separately.
- `250 GBX × 10 shares / 100 = GBP 25`. The conversion only reconciles pence
  and pounds; it does not convert USD, EUR or any other currency.
- Sum dividend `amount` within its stated `currency`. Do not substitute
  `grossAmountPerShare`, add `amountInEuro` to it or infer after-tax income.
- A zero denominator makes an allocation undefined. An empty holdings list does
  not imply that total account value or cash is zero.
- Describe reporting-window cash flows and observed P/L. Do not infer annualized,
  time-weighted, tax-adjusted or money-weighted returns from incomplete history.

## Synthetic examples

All figures below are fabricated and must never be presented as a user's account.

### Portfolio snapshot

Input: confirmed demo account; summary currency GBP, total value 1,000, investment
value 800, available cash 200. Position A wallet value GBP 500; position B wallet
value GBP 300. Metadata: cache hit, retrieved at 2026-10-23T09:00:00Z, TTL 15 seconds.

Expected report:

> Demo account snapshot, retrieved 23 October 2026 at 09:00 UTC (cached; TTL 15s).
> Total value GBP 1,000; investments GBP 800; available cash GBP 200.
> A represents 62.5% of holdings and B 37.5%. These are holdings allocations,
> excluding cash. This snapshot does not establish performance over a period.

### Mixed currencies and GBX

Input: 10 shares priced at 250 GBX; another holding worth USD 40; no wallet-impact
values or FX rates returned.

> The first holding is worth GBP 25 at the supplied price. The second is USD 40.
> A combined value and allocation are unavailable without comparable currency
> values. Environment and freshness are unconfirmed unless supplied separately.

### Dividends across pages

Input: requested October 2026; page one contains GBP 4 and a continuation; page two
contains GBP 6 and EUR 3, with no continuation. All dates fall in October.

> Returned October dividends total GBP 10 and EUR 3, reported separately.
> Both pages were retrieved. No FX conversion or tax adjustment was made.

If page two fails, report only GBP 4 as a retrieved subtotal and mark the period
incomplete. If no records were returned successfully, report no returned dividends;
if the request failed, report dividends unavailable.
