# Official source register

Verified 2026-09-19 against official documentation. Runtime smoke receipts are recorded separately; a documented capability is not a claim of a tested connection.

| Source / endpoint | Auth, pagination, budget | Fields and semantics |
|---|---|---|
| [Kalshi overview](https://docs.kalshi.com/welcome), `/trade-api/v2/series`, `/events`, `/events/{ticker}` | Public REST. Events cursor + limit, bounded series discovery. Local conservative 3 req/s per origin; actual tier/token budgets vary: [limits](https://docs.kalshi.com/getting_started/rate_limits). | Event/series tickers, nested markets, dollar/fixed-point fields, full primary/secondary rules. |
| [Kalshi books](https://docs.kalshi.com/getting_started/orderbook_responses), `/markets/{ticker}/orderbook` | Public; `depth=0` requests full book. | `orderbook_fp.yes_dollars/no_dollars`, [dollar string, quantity string]. NO bids become YES asks and vice versa at 1-price, retaining quantities. |
| [Kalshi candles](https://docs.kalshi.com/api-reference/market/get-market-candlesticks), `/series/{series}/markets/{ticker}/candlesticks` | Public; start_ts/end_ts/period_interval. | `price.close_dollars` is a trade candle close. `yes_bid/yes_ask.close_dollars` are distinct price types. Do not overlay with indicative history. |
| [Kalshi WebSocket](https://docs.kalshi.com/getting_started/quick_start_websockets) | Authenticated signed handshake. Local default has no credentials; use explicitly POLLED REST fallback. | Sequence-bearing book events require snapshot on gap. No private portfolio/order integration. |
| [Kalshi series fees](https://docs.kalshi.com/api-reference/market/get-series) | Public series metadata; event overrides may apply. | fee_type and fee_multiplier alone do not establish complete per-market/date fee policy. Live fee policy remains UNKNOWN until override/rounding evidence is resolved. |
| [Polymarket API surfaces](https://docs.polymarket.com/getting-started/api), Gamma `/public-search`, `/events?slug=` | Public. Search pagination; returned bounded 20 events here. | Events/markets, named outcomes mapped to token IDs, description, endDate, active/closed. |
| [Polymarket books/prices](https://docs.polymarket.com/market-data/prices-order-books), CLOB `/book?token_id=` | Public; independent YES and NO books. | bids/asks price,size, timestamp (milliseconds), hash, tick_size, min_order_size. Size is executable depth, not volume. |
| [Polymarket history](https://docs.polymarket.com/market-data/prices-order-books), Data API `/v2/prices-history` | Public token_id, interval or bounded range, bucket_seconds, cursor. | Price observations under data with pagination; price type is not guaranteed midpoint or trade. Label INDICATIVE. This endpoint is used for history only; CLOB remains executable-book authority. |
| [Polymarket realtime](https://docs.polymarket.com/market-data/realtime-data), `wss://ws-subscriptions-clob.polymarket.com/ws/market` | Public market subscription with assets_ids; application heartbeat PING/PONG. | No fabricated sequence guarantees. Event receipt invalidates the selected book and triggers conservative REST resnapshot; frontend labels pricing POLLED. |
| [Polymarket fees](https://docs.polymarket.com/trading/fees), [fee rate](https://docs.polymarket.com/api-reference/market-data/get-fee-rate) | Public market/token metadata; category/formula/effective-date evidence needed. | No automatic zero-fee assumption from missing fields. Scenario manual fee override does not produce verified net edge. |

All origins are hard-coded in adapters. URL import extracts identifiers from allowlisted hosts and never fetches the pasted URL. Redirects are disabled. Transport honors Retry-After, bounds concurrency/retries and exposes rate-limit errors. Raw public payloads are archived with retrieval timestamps and hashes; retention defaults to seven days. Upstream time and receipt time remain separate.

## Actual live receipt

Both supplied Fed URL import paths were rechecked at 2026-09-19 08:57:59 UTC. Each resolved two original/counterpart events and five unreviewed candidates. The selected comparison returned full books plus 124 Kalshi trade candles and 169 Polymarket indicative observations. No source errors occurred. These reads establish connectivity/schema behavior, not settlement equivalence or profitability. See verification.md.
