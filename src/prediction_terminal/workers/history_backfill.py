"""Bounded provider-history warmup; local bid/ask history comes from ingestion."""


async def backfill(c, market_id, days=7):
    m = c.comparison.market(market_id)
    return await c.comparison.history(m, "last_trade" if m.venue == "kalshi" else "indicative", days)
