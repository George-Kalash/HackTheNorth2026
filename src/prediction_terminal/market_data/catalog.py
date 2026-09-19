from uuid import uuid4

from prediction_terminal.domain.markets import Event
from prediction_terminal.domain.matches import MatchGroup
from prediction_terminal.matching.review import invalidate


def store_event(repo, event: Event):
    previous = repo.get("venue_events", event.id)
    active_ids = {m.id for m in event.markets}
    if previous:
        for old_market in previous.get("markets", []):
            if old_market["id"] not in active_ids:
                old_market["active"] = False
                repo.put(
                    "venue_markets",
                    old_market["id"],
                    old_market,
                    event_id=event.id,
                    venue=old_market["venue"],
                    external_id=old_market["external_id"],
                )
    repo.put(
        "venue_events",
        event.id,
        event.model_dump(mode="json"),
        venue=event.venue,
        external_id=event.external_id,
    )
    for market in event.markets:
        old = repo.get("venue_markets", market.id)
        repo.put(
            "venue_markets",
            market.id,
            market.model_dump(mode="json"),
            event_id=event.id,
            venue=market.venue,
            external_id=market.external_id,
        )
        for outcome in market.outcomes:
            repo.put(
                "outcomes",
                market.id + "_" + outcome.name,
                outcome.model_dump(mode="json"),
                market_id=market.id,
            )
        version_id = market.id + "_" + market.settlement.rule_hash[:24]
        repo.put("rule_versions", version_id, market.settlement.model_dump(mode="json"), market_id=market.id)
        if old and old["settlement"]["rule_hash"] != market.settlement.rule_hash:
            for row in repo.list("match_groups", 10000):
                if market.id in row["market_ids"]:
                    match = invalidate(MatchGroup.model_validate(row), market.id, market.settlement.rule_hash)
                    repo.put("match_groups", match.id, match.model_dump(mode="json"))
                    repo.put(
                        "match_reviews",
                        "review_" + uuid4().hex,
                        {
                            "match_id": match.id,
                            "action": "automatic_revoke",
                            "reason": match.review_reason,
                            "rule_hashes": match.rule_hashes,
                        },
                        match_id=match.id,
                    )
