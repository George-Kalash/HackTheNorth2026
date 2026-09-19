from prediction_terminal.domain.errors import SourceUnavailable
from prediction_terminal.domain.markets import Event, stable_id

from .mapper import event

BASE = "https://gamma-api.polymarket.com"


class Gamma:
    def __init__(self, http):
        self.http = http

    async def event(self, slug):
        data = await self.http.get(BASE, "/events", {"slug": slug})
        if not data:
            raise SourceUnavailable("Polymarket event not found; no substitute event was loaded.", 404)
        try:
            return event(data[0])
        except (ValueError, KeyError, TypeError) as exc:
            raise SourceUnavailable("Polymarket event schema drift: " + str(exc)) from exc

    async def search(self, query):
        data = await self.http.get(
            BASE, "/public-search", {"q": query, "limit_per_type": 20, "events_status": "active"}, ttl=60
        )
        return [
            Event(
                id=stable_id("event", "polymarket", e["slug"]),
                venue="polymarket",
                external_id=e["slug"],
                title=e["title"],
                source_url="https://polymarket.com/event/" + e["slug"],
            )
            for e in data.get("events", [])[:20]
        ]
