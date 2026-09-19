# Pricing and simulation methodology

All backend prices/quantities use Decimal. Markets retain separate last trade, indicative price, book bid/ask and midpoint fields. Missing prices stay null. Kalshi bids are complemented level by level: YES asks = 1 − NO bids; NO asks = 1 − YES bids. Quantities are preserved, duplicate price levels merged, and asks sorted ascending. Polymarket YES/NO token identity comes from named outcomes, not array positions.

## Three different outputs

1. Indicative gap: 100 × (Kalshi YES midpoint − Polymarket YES midpoint), only with two-sided books. It is not profit.
2. Executable pre-fee floor: minimum scenario payout − summed cost of consuming ask ladders at the requested size.
3. Estimated after-cost floor: pre-fee floor − modeled fees − explicit other/funding costs − optional adverse-move stress per matched unit.

Depth already accounts for price impact. The stress input models additional future adverse movement, not the same slippage twice. The terminal buys positive inventory only; an unwind estimate sells only the modeled filled inventory at current bids and excludes unwind fees/future moves.

Approved, identical $1 claims can use YES+NO constant-payout scenarios. Unapproved contracts also include a both-legs-lose scenario. Insufficient depth returns partial fills and no complete-pair net estimate. Non-$1 claims, stale/degraded/skewed books, unknown lot sizes, non-multiple lots, inactive contracts, unknown fees and denomination mismatches block verification. USD/pUSD 1:1 is explicitly a user assumption and retains a basis-risk eligibility reason.

Paired budget sizing consumes depth using known fees or an explicit total fee assumption. Unknown lot metadata uses a disclosed 0.01-unit scenario grid and remains unverified; it is not evidence that the venue accepts such orders. Size optimization uses cumulative depth breakpoints, common minimum lots and fee-aware interval search. The reported capacity is current quoted capacity, not reserved liquidity or guaranteed fills. Budget mode also sizes synthetic baskets across every leg. Synthetic threshold capacity uses complete payoff scenarios and reviewed fee policies.

Synthetic matrices list target YES and each basket YES payout for every declared state, including OTHER. Replication rejects missing columns, overlaps, uncovered states and nonbinary payouts. Default direction buys target NO + basket YES; reverse buys target YES + each basket NO. The minimum payout is evaluated across the whole matrix, never assumed to equal one. Coverage and actual rules still require approval. Automatic discovery of arbitrary synthetic baskets is not implemented.

## Fees

Live default is UNKNOWN. Missing fee data never implies zero. The settings editor can record a market-specific taker policy supported by current official evidence: zero, notional coefficient, or quadratic coefficient. Evidence includes market overrides/date/rounding, is versioned, and expires (UI default 24 hours, server maximum 31 days). It is a human-reviewed assertion, not automatic venue certification. Unsupported formulas stay unknown. The engine rounds supported policies up at the specified quantum; quadratic policies round per consumed price level. Actual fragmented fills can produce different rounding. Maker execution is not modeled; all immediate simulations are taker scenarios.

A manual total-fee input in the simulator is a scenario assumption only and never marks unknown fees verified. ROI is net floor divided by required modeled cash; no annualized return is displayed without a credible holding period. Capital helpers are available but the UI deliberately does not invent one.

## History

Kalshi provider charts show trade candle close. Polymarket Data API price observations are labeled indicative because the endpoint alone does not establish identical trade/midpoint semantics. They render separately. Local recorded midpoint/bid/ask series can be overlaid and aligned by UTC using backward as-of matching with a 120-second maximum age; missing intervals remain gaps. Recorded bid/ask history starts with this installation. No historical executable-arbitrage claim is reconstructed from last trades. Synthetic legs render individually, with a target-minus-sum spread only when every component has a like-type observation within 120 seconds. Incomplete intervals remain gaps; the component sum is a basket price, not a probability or executable profit.
