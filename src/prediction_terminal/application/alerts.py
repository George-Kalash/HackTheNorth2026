from datetime import datetime
from decimal import Decimal
from uuid import uuid4

from prediction_terminal.domain.markets import utcnow


def evaluate(repo, opportunity):
    if not opportunity.verified or opportunity.estimated_net_floor is None:
        return []
    events = []
    for rule in repo.list("alert_rules", 1000):
        if not rule.get("enabled") or rule.get("match_id") not in {None, opportunity.match_id}:
            continue
        if opportunity.estimated_net_floor < Decimal(rule["min_net_floor"]):
            continue
        previous = [e for e in repo.list("alert_events", 1000) if e["rule_id"] == rule["id"]]
        if (
            previous
            and (utcnow() - datetime.fromisoformat(previous[0]["created_at"])).total_seconds()
            < rule["cooldown_seconds"]
        ):
            continue
        event = {
            "id": "alert_" + uuid4().hex,
            "rule_id": rule["id"],
            "match_id": opportunity.match_id,
            "created_at": utcnow().isoformat(),
            "net_floor": str(opportunity.estimated_net_floor),
            "book_ids": opportunity.book_ids,
        }
        repo.put("alert_events", event["id"], event, rule_id=rule["id"])
        events.append(event)
    return events
