import asyncio
from datetime import timedelta

from prediction_terminal.domain.books import BookSnapshot
from prediction_terminal.domain.errors import TerminalError
from prediction_terminal.domain.history import PriceHistory, PricePoint
from prediction_terminal.domain.markets import VenueMarket, utcnow
from prediction_terminal.domain.matches import MatchGroup
from prediction_terminal.market_data.freshness import eligibility
from prediction_terminal.market_data.history import align, align_basket
from prediction_terminal.market_data.normalizer import quote


class ComparisonService:
    def __init__(self, feeds, repo, settings):
        self.feeds = feeds
        self.repo = repo
        self.settings = settings
        self.locks = {}

    def market(self, id):
        row = self.repo.get("venue_markets", id)
        if not row:
            raise TerminalError("NOT_FOUND", "Market not found.", 404)
        return VenueMarket.model_validate(row)

    def match(self, id):
        row = self.repo.get("match_groups", id)
        if not row:
            raise TerminalError("NOT_FOUND", "Match not found.", 404)
        return MatchGroup.model_validate(row)

    async def book(self, market, force=False):
        lock = self.locks.setdefault(market.id, asyncio.Lock())
        async with lock:
            old = self.repo.latest_book(market.id)
            if old and not force:
                cached = BookSnapshot.model_validate(old)
                if (utcnow() - cached.received_at).total_seconds() < self.settings.poll_seconds:
                    state = self.repo.get("ingestion_checkpoints", "feed_" + market.id)
                    if state and state.get("error"):
                        cached.flags = list(set(cached.flags + ["DISCONNECTED", state["error"]]))
                    return cached
            try:
                b = await self.feeds[market.venue].book(market)
                for side in ["YES", "NO"]:
                    q = quote(b, side)
                    if q.bid is not None and q.ask is not None and q.bid > q.ask:
                        b.flags.append("CROSSED")
                self.repo.put("book_snapshots", b.id, b.model_dump(mode="json"), market_id=market.id)
                q = quote(b)
                self.repo.put(
                    "price_points",
                    b.id,
                    {
                        "id": b.id,
                        "market_id": market.id,
                        "time": b.received_at.isoformat(),
                        "midpoint": str(q.midpoint) if q.midpoint is not None else None,
                        "bid": str(q.bid) if q.bid is not None else None,
                        "ask": str(q.ask) if q.ask is not None else None,
                    },
                    market_id=market.id,
                )
                self.repo.put(
                    "ingestion_checkpoints",
                    "feed_" + market.id,
                    {"id": "feed_" + market.id, "error": None, "received_at": b.received_at.isoformat()},
                )
                return b
            except TerminalError as exc:
                self.repo.put(
                    "ingestion_checkpoints",
                    "feed_" + market.id,
                    {"id": "feed_" + market.id, "error": exc.message, "received_at": utcnow().isoformat()},
                )
                if old:
                    b = BookSnapshot.model_validate(old)
                    b.flags = list(set(b.flags + ["DISCONNECTED", exc.message]))
                    return b
                return BookSnapshot(
                    market_id=market.id, mode="UNAVAILABLE", flags=[exc.message, "DISCONNECTED"]
                )

    async def get(self, id, days=7, history_type="provider", with_history=True):
        match = self.match(id)
        markets = [self.market(m) for m in match.market_ids]
        self.repo.put(
            "ingestion_checkpoints",
            "selected_" + id,
            {
                "id": "selected_" + id,
                "match_id": id,
                "expires_at": (utcnow() + timedelta(minutes=3)).isoformat(),
            },
        )
        books = await asyncio.gather(*(self.book(m) for m in markets))
        quotes = [quote(b) for b in books]
        gap = (
            (quotes[0].midpoint - quotes[1].midpoint) * 100
            if len(quotes) == 2 and quotes[0].midpoint is not None and quotes[1].midpoint is not None
            else None
        )
        histories = []
        errors = []
        if with_history:
            for market in markets:
                typ = (
                    ("last_trade" if market.venue == "kalshi" else "indicative")
                    if history_type == "provider"
                    else history_type
                )
                try:
                    histories.append(await self.history(market, typ, days))
                except TerminalError as exc:
                    errors.append(exc.message)
                    histories.append(
                        PriceHistory(
                            market_id=market.id,
                            price_type=typ,
                            source="Unavailable",
                            points=[],
                            interval_seconds=3600,
                            warnings=[exc.message],
                        )
                    )
        aligned, warnings = (
            align(histories[0], histories[1], max_age_seconds=120)
            if len(histories) == 2
            else align_basket(histories)
            if len(histories) > 2
            else ([], [])
        )
        return {
            "match": match.model_dump(mode="json"),
            "markets": [m.model_dump(mode="json") for m in markets],
            "books": [b.model_dump(mode="json") for b in books],
            "quotes": [q.model_dump(mode="json") for q in quotes],
            "indicative_gap_pp": str(gap) if gap is not None else None,
            "histories": [h.model_dump(mode="json") for h in histories],
            "aligned": aligned,
            "history_warnings": warnings,
            "eligibility_reasons": eligibility(
                books, utcnow(), self.settings.max_age_seconds, self.settings.max_skew_seconds
            ),
            "errors": errors,
            "received_at": utcnow().isoformat(),
            "mode": "POLLED",
        }

    async def history(self, market, price_type, days):
        if price_type in {"midpoint", "bid", "ask"}:
            rows = self.repo.list("price_points", 10000)
            cutoff = utcnow() - timedelta(days=days)
            from datetime import datetime

            points = [
                PricePoint(time=row["time"], price=row[price_type])
                for row in rows
                if row["market_id"] == market.id
                and row.get(price_type) is not None
                and datetime.fromisoformat(row["time"]) >= cutoff
            ]
            return PriceHistory(
                market_id=market.id,
                price_type=price_type,
                source="Local recorded normalized books / receipt UTC",
                points=sorted(points, key=lambda p: p.time),
                interval_seconds=int(self.settings.poll_seconds),
                warnings=[
                    "History starts with this installation; receipt-time samples, not past executable depth."
                ],
            )
        return await self.feeds[market.venue].history(market, price_type, days)

    async def history_range(self, market, price_type, days, start=None, end=None, interval=None):
        from datetime import timedelta
        from math import ceil

        now = utcnow()
        end = end or now
        start = start or end - timedelta(days=days)
        if start.tzinfo is None or end.tzinfo is None or start >= end or end > now + timedelta(minutes=1):
            raise TerminalError(
                "INVALID_HISTORY_RANGE",
                "Use ordered UTC-aware from/to timestamps ending no later than now",
                422,
            )
        if (now - start).total_seconds() > 30 * 86400:
            raise TerminalError(
                "HISTORY_RANGE_UNSUPPORTED",
                "This release supports the most recent 30 days; older local/provider history is not substituted",
                422,
            )
        age = ceil((now - start).total_seconds() / 86400)
        window = 1 if age <= 1 else 7 if age <= 7 else 30
        history = await self.history(market, price_type, window)
        points = [p for p in history.points if start <= p.time <= end]
        if interval:
            seconds = {"1m": 60, "1h": 3600, "1d": 86400}[interval]
            # Last actual observation per requested UTC bucket; preserve actual timestamp.
            buckets = {int(p.time.timestamp()) // seconds: p for p in sorted(points, key=lambda p: p.time)}
            points = list(buckets.values())
            history.interval_seconds = seconds
        history.points = points
        return history
