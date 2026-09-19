import json
from datetime import UTC, datetime
from decimal import Decimal

from prediction_terminal.domain.books import BookSnapshot
from prediction_terminal.domain.markets import Event, Outcome, VenueMarket, stable_id
from prediction_terminal.market_data.normalizer import levels
from prediction_terminal.matching.predicates import settlement

from .schemas import WireBook


def array(value):
    return json.loads(value) if isinstance(value, str) else value or []


def event(raw):
    eid = stable_id("event", "polymarket", raw["slug"])
    url = "https://polymarket.com/event/" + raw["slug"]
    markets = []
    for m in raw.get("markets", []):
        outcomes = array(m.get("outcomes"))
        tokens = array(m.get("clobTokenIds"))
        prices = array(m.get("outcomePrices"))
        if {o.lower() for o in outcomes} != {"yes", "no"} or len(tokens) != 2:
            continue
        yi = [o.lower() for o in outcomes].index("yes")
        spec = settlement(m.get("description") or raw.get("description", ""), "pUSD")
        spec.deadline = m.get("endDate")
        markets.append(
            VenueMarket(
                id=stable_id("market", "polymarket", str(m["id"])),
                venue="polymarket",
                external_id=str(m["id"]),
                event_id=eid,
                title=m["question"],
                outcome=m.get("groupItemTitle") or m["question"],
                source_url=url,
                slug=raw["slug"],
                condition_id=m.get("conditionId"),
                active=bool(m.get("active") and not m.get("closed")),
                close_time=m.get("endDate"),
                outcomes=[Outcome(name=o.upper(), token_id=t) for o, t in zip(outcomes, tokens)],
                settlement=spec,
                indicative=prices[yi] if len(prices) == 2 else None,
                last_trade=m.get("lastTradePrice"),
                raw_units="pUSD / outcome tokens",
            )
        )
    return Event(
        id=eid,
        venue="polymarket",
        external_id=raw["slug"],
        title=raw["title"],
        source_url=url,
        markets=markets,
    )


def book(yes_raw, no_raw, market):
    yes, no = WireBook.model_validate(yes_raw), WireBook.model_validate(no_raw)
    ids = {o.name: o.token_id for o in market.outcomes}
    if yes.asset_id != ids["YES"] or no.asset_id != ids["NO"]:
        raise ValueError("Token identity mismatch")
    times = [datetime.fromtimestamp(int(b.timestamp) / 1000, UTC) for b in [yes, no]]
    flags = []
    if abs((times[0] - times[1]).total_seconds()) > 20:
        flags.append("TOKEN_TIME_SKEW")
    return BookSnapshot(
        market_id=market.id,
        yes_bids=levels(yes.bids, True),
        yes_asks=levels(yes.asks),
        no_bids=levels(no.bids, True),
        no_asks=levels(no.asks),
        venue_time=min(times),
        source_hash=yes.hash + ":" + no.hash,
        lot_size=max(Decimal(yes.min_order_size or "0"), Decimal(no.min_order_size or "0")) or None,
        tick_size=yes.tick_size,
        flags=flags,
    )
