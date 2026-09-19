from datetime import datetime, timezone


def compare(k, p, allowance=0.0):
    gap = (
        None
        if k.probability is None or p.probability is None
        else (k.probability - p.probability) * 100
    )
    trades = []
    # Each pair buys one YES and one NO on different venues. No short inventory needed.
    for yes, no in [(k, p), (p, k)]:
        if not yes.active or not no.active or yes.yes_ask is None or no.no_ask is None:
            continue
        if yes.yes_ask <= 0 or no.no_ask <= 0:
            continue
        stale = False
        for market in [yes, no]:
            if market.quote_time:
                age = (
                    datetime.now(timezone.utc) - datetime.fromisoformat(market.quote_time)
                ).total_seconds()
                stale |= age > 120
        cost = yes.yes_ask + no.no_ask
        sizes = [yes.yes_size, no.no_size]
        trades.append(
            {
                "yes_platform": yes.platform,
                "no_platform": no.platform,
                "yes_price": yes.yes_ask,
                "no_price": no.no_ask,
                "cost": round(cost, 6),
                "gross_edge": round(1 - cost, 6),
                "adjusted_edge": round(1 - cost - allowance, 6),
                "allowance": allowance,
                "stale": stale,
                "max_pairs_at_top": min(sizes) if all(s is not None for s in sizes) else None,
                "status": "Stale quote — refresh before evaluating"
                if stale
                else "Conditional estimate — settlement equivalence unverified",
            }
        )
    trades.sort(key=lambda t: t["adjusted_edge"], reverse=True)
    return {"gap_pp": round(gap, 4) if gap is not None else None, "trades": trades}
