import asyncio
from datetime import UTC, datetime

from prediction_terminal.domain.errors import SourceUnavailable
from prediction_terminal.domain.history import PriceHistory, PricePoint

from .gamma import Gamma
from .mapper import book

BASE = "https://clob.polymarket.com"
DATA = "https://data-api.polymarket.com"


class PolymarketFeed(Gamma):
    async def book(self, market):
        ids = {o.name: o.token_id for o in market.outcomes}
        raw = await asyncio.gather(
            *(self.http.get(BASE, "/book", {"token_id": ids[side]}) for side in ["YES", "NO"])
        )
        try:
            result = book(raw[0], raw[1], market)
            result.raw_source_ids = [self.http.raw_id(data) for data in raw]
            return result
        except (ValueError, KeyError, TypeError) as exc:
            raise SourceUnavailable("Polymarket book schema drift: " + str(exc)) from exc

    async def history(self, market, price_type, days):
        if price_type != "indicative":
            return PriceHistory(
                market_id=market.id,
                price_type=price_type,
                source="Recorded local books",
                points=[],
                interval_seconds=60,
                warnings=["Provider observations do not establish this price type. Local snapshots only."],
            )
        token = next(o.token_id for o in market.outcomes if o.name == "YES")
        points = []
        cursor = None
        for _ in range(20):
            params = {
                "token_id": token,
                "interval": {1: "1d", 7: "1w", 30: "1m"}[days],
                "bucket_seconds": 3600 if days <= 7 else 86400,
            }
            if cursor:
                params["cursor"] = cursor
            data = await self.http.get(DATA, "/v2/prices-history", params, ttl=60)
            for p in data.get("data", []):
                stamp = p["timestamp"]
                dt = (
                    datetime.fromtimestamp(stamp, UTC)
                    if isinstance(stamp, (int, float))
                    else datetime.fromisoformat(stamp)
                )
                points.append(PricePoint(time=dt, price=p["price"]))
            pagination = data.get("pagination", {})
            if not pagination.get("has_more"):
                break
            cursor = pagination.get("next_cursor")
            if not cursor:
                raise SourceUnavailable("History pagination metadata incomplete")
        else:
            raise SourceUnavailable("History pagination limit reached; shorten the requested range")
        return PriceHistory(
            market_id=market.id,
            price_type="indicative",
            source=DATA + "/v2/prices-history",
            points=points,
            interval_seconds=3600 if days <= 7 else 86400,
            warnings=["Provider price observations; not historical executable depth."],
        )
