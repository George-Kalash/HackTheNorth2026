import asyncio
import json
from urllib.parse import quote

from marketlens.clients.http import SourceError
from marketlens.models import Event, Market, now, price

GAMMA = "https://gamma-api.polymarket.com"
CLOB = "https://clob.polymarket.com"
DATA = "https://data-api.polymarket.com"


def array(value):
    return json.loads(value) if isinstance(value, str) else value or []


def normalize(m, event):
    outcomes = array(m.get("outcomes"))
    if {str(o).lower() for o in outcomes} != {"yes", "no"}:
        return None
    yi = [o.lower() for o in outcomes].index("yes")
    ni = 1 - yi
    prices, tokens = array(m.get("outcomePrices")), array(m.get("clobTokenIds"))
    return Market(
        platform="Polymarket",
        id=str(m["id"]),
        event_id=event["slug"],
        title=m["question"],
        outcome=m.get("groupItemTitle") or m["question"],
        url=f"https://polymarket.com/event/{quote(event['slug'], safe='')}",
        rules=m.get("description") or event.get("description", ""),
        close_time=m.get("endDate"),
        active=bool(m.get("active") and not m.get("closed")),
        probability=price(prices[yi]) if len(prices) > yi else None,
        probability_basis="Gamma indicative price (may be stale)",
        token_yes=tokens[yi] if len(tokens) > yi else None,
        token_no=tokens[ni] if len(tokens) > ni else None,
    )


class Polymarket:
    def __init__(self, http):
        self.http = http

    async def event(self, slug):
        data = await self.http.get(GAMMA, "/events", {"slug": slug}, ttl=0)
        if not data:
            raise SourceError("Polymarket event not found. Paste an event URL or slug.")
        e = data[0]
        return Event(
            platform="Polymarket",
            id=e["slug"],
            title=e["title"],
            markets=[n for m in e.get("markets", []) if (n := normalize(m, e))],
        )

    async def search(self, query):
        data = await self.http.get(
            GAMMA,
            "/public-search",
            {"q": query, "limit_per_type": 20, "events_status": "active"},
            ttl=60,
        )
        return [
            Event(platform="Polymarket", id=e["slug"], title=e["title"])
            for e in data.get("events", [])[:20]
        ]

    async def refresh(self, market):
        if not market.active or not market.token_yes or not market.token_no:
            return market
        try:
            books = await asyncio.gather(
                *(
                    self.http.get(CLOB, "/book", {"token_id": token}, ttl=0)
                    for token in [market.token_yes, market.token_no]
                )
            )
            for side, book in zip(["yes", "no"], books):
                asks = [(price(a["price"]), float(a["size"])) for a in book.get("asks", [])]
                asks = [(p, s) for p, s in asks if p is not None and s > 0]
                if asks:
                    p, size = min(asks)
                    setattr(market, f"{side}_ask", p)
                    setattr(market, f"{side}_size", sum(s for q, s in asks if q == p))
            bids = [price(b["price"]) for b in books[0].get("bids", []) if float(b["size"]) > 0]
            bids = [p for p in bids if p is not None]
            if bids and market.yes_ask is not None and max(bids) <= market.yes_ask:
                market.probability = (max(bids) + market.yes_ask) / 2
                market.probability_basis = "YES bid/ask midpoint"
            stamps = [int(b["timestamp"]) / 1000 for b in books if b.get("timestamp")]
            if len(stamps) == 2:
                from datetime import datetime, timezone

                market.quote_time = datetime.fromtimestamp(min(stamps), timezone.utc).isoformat()
            market.fetched_at = now()
        except SourceError as exc:
            market.warnings.append(f"Live order book unavailable: {exc}")
        return market

    async def history(self, market, days):
        if not market.token_yes:
            return []
        points, cursor = [], None
        for _ in range(20):
            params = {
                "token_id": market.token_yes,
                "interval": {1: "1d", 7: "1w", 30: "1m"}[days],
                "bucket_seconds": 3600 if days <= 7 else 86400,
            }
            if cursor:
                params["cursor"] = cursor
            data = await self.http.get(DATA, "/v2/prices-history", params, ttl=60)
            points.extend(
                {"t": p["timestamp"], "p": price(p["price"])}
                for p in data.get("data", [])
                if price(p.get("price")) is not None
            )
            page = data.get("pagination", {})
            if not page.get("has_more"):
                return points
            cursor = page.get("next_cursor")
            if not cursor:
                break
        raise SourceError("History pagination limit reached; choose a shorter range.")
