import asyncio
import re
from urllib.parse import urlparse

from prediction_terminal.domain.errors import TerminalError
from prediction_terminal.market_data.catalog import store_event
from prediction_terminal.matching.candidates import propose

SEEDS = {"KXFEDDECISION-26OCT": "fed-decision-in-october-20260617190323537"}


def parse_url(url):
    u = urlparse(url.strip())
    try:
        port = u.port
    except ValueError as exc:
        raise TerminalError("INVALID_URL", "Invalid venue URL port", 422) from exc
    if u.scheme != "https" or u.username or u.password or port not in {None, 443}:
        raise TerminalError("INVALID_URL", "Use a public HTTPS venue event URL.", 422)
    parts = u.path.strip("/").split("/")
    if u.hostname in {"kalshi.com", "www.kalshi.com"} and len(parts) in {3, 4} and parts[0] == "markets":
        external = parts[-1].upper()
        venue = "kalshi"
    elif u.hostname in {"polymarket.com", "www.polymarket.com"} and len(parts) == 2 and parts[0] == "event":
        external = parts[1]
        venue = "polymarket"
    else:
        raise TerminalError(
            "INVALID_URL", "Only known Kalshi market and Polymarket event URLs are supported.", 422
        )
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,250}", external):
        raise TerminalError("INVALID_URL", "Invalid event identifier.", 422)
    return venue, external


class SearchService:
    def __init__(self, feeds, repo):
        self.feeds = feeds
        self.repo = repo

    async def search(self, q):
        if "://" in q:
            return await self.import_url(q)
        results = await asyncio.gather(*(f.search(q) for f in self.feeds.values()), return_exceptions=True)
        return {
            "events": [
                e.model_dump(mode="json") for r in results if not isinstance(r, BaseException) for e in r
            ],
            "matches": [],
            "errors": [str(r) for r in results if isinstance(r, BaseException)],
            "coverage": "Bounded search: top six Kalshi series (up to three event pages each); first 20 Polymarket events. Not exhaustive.",
        }

    async def import_url(self, url):
        venue, external = parse_url(url)
        original = await self.feeds[venue].event(external)
        store_event(self.repo, original)
        other = "polymarket" if venue == "kalshi" else "kalshi"
        counterpart = (
            SEEDS.get(external)
            if venue == "kalshi"
            else next((k for k, v in SEEDS.items() if v == external), None)
        )
        events = [original]
        errors = []
        try:
            if counterpart:
                peers = [await self.feeds[other].event(counterpart)]
            else:
                year = (
                    str(original.markets[0].close_time.year)
                    if original.markets and original.markets[0].close_time
                    else ""
                )
                results = await self.feeds[other].search(original.title + " " + year)
                peers = await asyncio.gather(
                    *(self.feeds[other].event(e.external_id) for e in results[:3]), return_exceptions=True
                )
            for peer in peers:
                if isinstance(peer, BaseException):
                    errors.append(str(peer))
                    continue
                store_event(self.repo, peer)
                events.append(peer)
        except TerminalError as exc:
            errors.append(exc.message)
        matches = []
        for peer in events[1:]:
            for a in original.markets:
                for b in peer.markets:
                    k, p = (a, b) if a.venue == "kalshi" else (b, a)
                    match = propose(k, p)
                    if match:
                        old = self.repo.get("match_groups", match.id)
                        if old and old["rule_hashes"] == match.rule_hashes:
                            from prediction_terminal.domain.matches import MatchGroup

                            match = MatchGroup.model_validate(old)
                        self.repo.put("match_groups", match.id, match.model_dump(mode="json"))
                        for index, leg in enumerate(match.legs):
                            self.repo.put(
                                "match_legs",
                                match.id + "_" + str(index),
                                leg.model_dump(mode="json"),
                                match_id=match.id,
                                market_id=leg.market_id,
                            )
                        matches.append(match.model_dump(mode="json"))
        return {
            "events": [e.model_dump(mode="json") for e in events],
            "matches": sorted(matches, key=lambda m: m["score"], reverse=True),
            "errors": errors,
            "coverage": "Original event plus evidence-bearing candidate events. Seed URLs identify candidates only.",
        }
