import asyncio
import re
import time
from urllib.parse import quote

from marketlens.matching import similarity
from marketlens.models import Event, Market, now, price

BASE = "https://api.elections.kalshi.com/trade-api/v2"


def dollars(m, key):
    if key + "_dollars" in m:
        return price(m[key + "_dollars"])
    return price(float(m[key]) / 100) if m.get(key) is not None else None


def normalize(m, event):
    bid, ask = dollars(m, "yes_bid"), dollars(m, "yes_ask")
    no_ask = dollars(m, "no_ask")
    yes_size = m.get("yes_ask_size_fp")
    no_size = m.get("yes_bid_size_fp")  # A YES bid is the corresponding NO ask.
    if (yes_size is not None and float(yes_size) <= 0) or ask in {0, 1}:
        ask = None
    if bid in {None, 0} or (no_size is not None and float(no_size) <= 0):
        no_ask = None
    # Zero bid / size means there may be no live bid, so don't invent a midpoint.
    two_sided = bid is not None and ask is not None and 0 < bid <= ask < 1
    probability = (bid + ask) / 2 if two_sided else dollars(m, "last_price")
    return Market(
        platform="Kalshi",
        id=m["ticker"],
        event_id=event["event_ticker"],
        title=m["title"],
        outcome=m.get("yes_sub_title") or m.get("subtitle") or m["title"],
        url=f"https://kalshi.com/markets/{event['series_ticker'].lower()}/{event['event_ticker'].lower()}",
        rules="\n\n".join(filter(None, [m.get("rules_primary"), m.get("rules_secondary")])),
        close_time=m.get("close_time"),
        active=m.get("status") in {"active", "open"},
        probability=probability,
        probability_basis="YES bid/ask midpoint" if two_sided else "Last trade (may be stale)",
        yes_ask=ask,
        no_ask=no_ask,
        yes_size=yes_size,
        no_size=no_size,
        series=event["series_ticker"],
        warnings=["Quote timestamp unavailable; retrieval time is not exchange freshness."],
    )


class Kalshi:
    def __init__(self, http):
        self.http = http

    async def event(self, ticker):
        data = await self.http.get(
            BASE,
            f"/events/{quote(ticker.upper(), safe='')}",
            {"with_nested_markets": "true"},
            ttl=0,
        )
        event = data["event"]
        return Event(
            platform="Kalshi",
            id=event["event_ticker"],
            title=event["title"],
            markets=[normalize(m, event) for m in event.get("markets") or data.get("markets", [])],
        )

    async def search(self, query):
        data = await self.http.get(BASE, "/series", ttl=600)
        # Series titles omit individual event months; rank the subject first.
        topic = (
            re.sub(
                r"\b(?:20\d{2}|jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?|decision|meeting)\b",
                " ",
                query,
                flags=re.IGNORECASE,
            ).strip()
            or query
        )
        ranked = sorted(
            data.get("series", []),
            key=lambda s: similarity(topic, s["title"] + " " + s["ticker"]),
            reverse=True,
        )
        selected = [
            s for s in ranked[:6] if similarity(topic, s["title"] + " " + s["ticker"]) > 0.1
        ]

        async def events(s):
            result = []
            cursor = ""
            for _ in range(3):
                d = await self.http.get(
                    BASE,
                    "/events",
                    {
                        "series_ticker": s["ticker"],
                        "status": "open",
                        "limit": 200,
                        "cursor": cursor,
                    },
                    ttl=60,
                )
                result.extend(d.get("events", []))
                cursor = d.get("cursor")
                if not cursor:
                    break
            return result

        groups = await asyncio.gather(*(events(s) for s in selected))
        results = [e for group in groups for e in group]
        results.sort(
            key=lambda e: similarity(query, e["title"] + " " + e.get("sub_title", "")), reverse=True
        )
        return [
            Event(platform="Kalshi", id=e["event_ticker"], title=e["title"]) for e in results[:20]
        ]

    async def history(self, market, days):
        end = int(time.time())
        data = await self.http.get(
            BASE,
            f"/series/{quote(market.series, safe='')}/markets/{quote(market.id, safe='')}/candlesticks",
            {
                "start_ts": end - days * 86400,
                "end_ts": end,
                "period_interval": 60 if days <= 7 else 1440,
            },
            ttl=60,
        )
        return [
            {"t": c["end_period_ts"], "p": p}
            for c in data.get("candlesticks", [])
            if (p := dollars(c.get("price", {}), "close")) is not None
        ]

    async def refresh(self, market):
        # Event GET with ttl=0 already supplies the current top-of-book fields.
        market.fetched_at = now()
        return market
