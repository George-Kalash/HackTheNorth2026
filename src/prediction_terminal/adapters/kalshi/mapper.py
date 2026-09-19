from prediction_terminal.domain.books import BookSnapshot
from prediction_terminal.domain.markets import Event, Outcome, VenueMarket, stable_id
from prediction_terminal.market_data.normalizer import complement, levels
from prediction_terminal.matching.predicates import settlement

from .schemas import WireBook, WireMarket


def event(raw):
    e = raw["event"]
    eid = stable_id("event", "kalshi", e["event_ticker"])
    url = f"https://kalshi.com/markets/{e['series_ticker'].lower()}/{e['event_ticker'].lower()}"
    markets = []
    for m in e.get("markets") or raw.get("markets", []):
        WireMarket.model_validate(m)
        rules = "\n\n".join(filter(None, [m.get("rules_primary"), m.get("rules_secondary")]))
        spec = settlement(rules)
        spec.deadline = m.get("expiration_time")
        spec.payout = m.get("notional_value_dollars", "1")
        markets.append(
            VenueMarket(
                id=stable_id("market", "kalshi", m["ticker"]),
                venue="kalshi",
                external_id=m["ticker"],
                event_id=eid,
                title=m["title"],
                outcome=m.get("yes_sub_title") or m.get("subtitle") or m["title"],
                source_url=url,
                series=e["series_ticker"],
                category=e.get("category", ""),
                active=m.get("status") in {"active", "open"},
                close_time=m.get("close_time"),
                outcomes=[Outcome(name="YES"), Outcome(name="NO")],
                settlement=spec,
                last_trade=m.get("last_price_dollars"),
                tick_size=None,
                lot_size=None,
            )
        )
    return Event(
        id=eid,
        venue="kalshi",
        external_id=e["event_ticker"],
        title=e["title"],
        source_url=url,
        markets=markets,
    )


def book(raw, market):
    wire = WireBook.model_validate(raw)
    if "orderbook_fp" not in raw:
        raise ValueError("Missing fixed-point book schema")
    yes = levels(wire.orderbook_fp.get("yes_dollars") or [], True)
    no = levels(wire.orderbook_fp.get("no_dollars") or [], True)
    return BookSnapshot(
        market_id=market.id,
        yes_bids=yes,
        no_bids=no,
        yes_asks=complement(no),
        no_asks=complement(yes),
        flags=["RECEIPT_TIME_FALLBACK", "LOT_SIZE_UNVERIFIED"],
        lot_size=None,
    )
