# Sources and interpretation

## Source contracts

- [Kalshi API](https://docs.kalshi.com/welcome): public series, events and markets from `https://api.elections.kalshi.com/trade-api/v2`. The adapter uses dollar-denominated fixed-point fields; legacy cent fields are converted only when the dollar field is absent.
- [Kalshi candles](https://docs.kalshi.com/api-reference/market/get-market-candlesticks): hourly trade closes for 1/7 days; daily closes for 30 days. Missing closes are omitted. Settled markets older than the historical cutoff may require the historical endpoint, not yet integrated.
- [Polymarket API](https://docs.polymarket.com/getting-started/api): Gamma event lookup and public search. Only binary Yes/No outcomes are supported; token indices are derived from outcome names rather than assumed.
- [Polymarket prices](https://docs.polymarket.com/market-data/prices-order-books): CLOB YES and NO order books supply independent best buy prices and sizes. Data API `/v2/prices-history` supplies price observations with cursor pagination. History uses common requested ranges but does not imply identical sampling or price methodology.

## Metrics

Probability is the YES bid/ask midpoint when a valid two-sided quote is present. Kalshi falls back to last trade; Polymarket to Gamma's indicative outcome price. Fallbacks are labeled and are not treated as executable buy prices. Missing values remain null, not zero.

Gap (percentage points) = 100 × (Kalshi YES probability − Polymarket YES probability). The UI headline displays its absolute value and names the higher venue.

For one YES on venue A and one NO on venue B:

- Entry cost = A YES ask + B NO ask.
- Gross conditional edge = 1 − entry cost.
- Adjusted conditional edge = gross edge − user-entered fee/slippage allowance.

Both directions are evaluated; the cheaper pair is displayed, including negative edges. The $1 payout only holds if the contracts settle identically. This is not asserted by text matching. Allowance is a flat dollar amount per pair, not an official fee schedule. Funding/withdrawal costs, currency/collateral differences, fill simultaneity, and depth beyond the best level are not modeled. Pair size is only shown when both side sizes are known.

## Matching and coverage

General suggestions use token overlap and text similarity. Fed outcomes additionally normalize hold, 25 bp cut/hike, and larger cut/hike labels. A >25 bp bucket and a 50+ bp bucket are related candidates, not proven equal: rounding rules can differ. Close times more than two days apart reduce ranking. No score certifies settlement equivalence. All pairs retain an unverified status, including user-selected pairs.

Kalshi search ranks the public series catalog, loads up to three 200-event pages from six series, and returns the best 20 events. Polymarket uses the first 20 public-search events. Results are not an exhaustive market scan; event URLs/tickers bypass search. General queries can miss event-specific entities absent from series titles. The supplied October 2026 links are a convenience preset, not an asserted profitable trade.

## Freshness and failures

Comparisons fetch current event metadata and fresh Polymarket books. Displayed retrieval timestamps are local receipt times, not guaranteed exchange update times. Kalshi event metadata does not provide a reliable quote timestamp here; that limitation is shown. Polymarket's oldest of the two book timestamps is exposed and quotes over 120 seconds old are flagged. The dashboard optionally polls every 30 seconds. Search caches for 60 seconds, series for 10 minutes, and history for 60 seconds. Source failures and missing history are displayed, never replaced by demo data. Quotes from two exchanges are not atomic.

The browser renders local SVG history charts from API data, rather than embedding platform pages. No chart CDN or external frontend dependency is required.
