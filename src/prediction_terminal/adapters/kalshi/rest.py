import asyncio
import re
import time
from datetime import UTC, datetime
from urllib.parse import quote

from prediction_terminal.domain.errors import SourceUnavailable
from prediction_terminal.domain.history import PriceHistory, PricePoint
from prediction_terminal.domain.markets import Event, stable_id
from prediction_terminal.matching.candidates import similarity

from .mapper import book, event

BASE = "https://api.elections.kalshi.com/trade-api/v2"


class KalshiFeed:
    def __init__(self, http):
        self.http = http

    async def event(self, external_id):
        raw = await self.http.get(
            BASE, "/events/" + quote(external_id.upper(), safe=""), {"with_nested_markets": "true"}
        )
        try:
            return event(raw)
        except (ValueError, KeyError, TypeError) as exc:
            raise SourceUnavailable("Kalshi event schema drift: " + str(exc)) from exc

    async def search(self, query):
        data = await self.http.get(BASE, "/series", ttl=600)
        topic = (
            re.sub(
                r"\b(?:20\d{2}|jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?|decision|meeting)\b",
                " ",
                query,
                flags=re.I,
            ).strip()
            or query
        )
        series = sorted(
            data.get("series", []),
            key=lambda s: similarity(topic, s["title"] + " " + s["ticker"]),
            reverse=True,
        )[:6]

        async def load(s):
            rows = []
            cursor = ""
            for _ in range(3):
                d = await self.http.get(
                    BASE,
                    "/events",
                    {"series_ticker": s["ticker"], "status": "open", "limit": 200, "cursor": cursor},
                    ttl=60,
                )
                rows.extend(d.get("events", []))
                cursor = d.get("cursor")
                if not cursor:
                    break
            return rows

        results = await asyncio.gather(*(load(s) for s in series))
        rows = sorted(
            [e for group in results for e in group],
            key=lambda e: similarity(query, e["title"] + " " + e.get("sub_title", "")),
            reverse=True,
        )
        return [
            Event(
                id=stable_id("event", "kalshi", e["event_ticker"]),
                venue="kalshi",
                external_id=e["event_ticker"],
                title=e["title"],
                source_url=f"https://kalshi.com/markets/{e['series_ticker'].lower()}/{e['event_ticker'].lower()}",
            )
            for e in rows[:20]
        ]

    async def book(self, market):
        raw = await self.http.get(
            BASE, f"/markets/{quote(market.external_id, safe='')}/orderbook", {"depth": 0}
        )
        try:
            result = book(raw, market)
            result.raw_source_ids = [self.http.raw_id(raw)]
            return result
        except (ValueError, KeyError, TypeError) as exc:
            raise SourceUnavailable("Kalshi book schema drift: " + str(exc)) from exc

    async def history(self, market, price_type, days):
        if price_type not in {"last_trade", "bid", "ask"}:
            return PriceHistory(
                market_id=market.id,
                price_type=price_type,
                source="Recorded local books",
                points=[],
                interval_seconds=60,
                warnings=["This price type starts when valid local snapshots are recorded."],
            )
        end = int(time.time())
        interval = 60 if days <= 7 else 1440
        d = await self.http.get(
            BASE,
            f"/series/{quote(market.series, safe='')}/markets/{quote(market.external_id, safe='')}/candlesticks",
            {"start_ts": end - days * 86400, "end_ts": end, "period_interval": interval},
            ttl=60,
        )
        key = {"last_trade": "price", "bid": "yes_bid", "ask": "yes_ask"}[price_type]
        points = [
            PricePoint(time=datetime.fromtimestamp(c["end_period_ts"], UTC), price=c[key]["close_dollars"])
            for c in d.get("candlesticks", [])
            if c.get(key, {}).get("close_dollars") is not None
        ]
        return PriceHistory(
            market_id=market.id,
            price_type=price_type,
            source=BASE + "/series/.../candlesticks",
            points=points,
            interval_seconds=interval * 60,
        )
