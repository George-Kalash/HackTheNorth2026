from datetime import datetime

from prediction_terminal.domain.markets import utcnow


def selected_matches(repo):
    ids = {i for w in repo.list("watchlists", 100) for i in w["match_ids"]}
    for row in repo.list("ingestion_checkpoints", 1000):
        if (
            row.get("match_id")
            and row.get("expires_at")
            and datetime.fromisoformat(row["expires_at"]) > utcnow()
        ):
            ids.add(row["match_id"])
    ids.update(m["id"] for m in repo.list("match_groups", 1000) if m["review_state"] == "APPROVED")
    return sorted(ids)[:30]


async def ingest(c, ids, force=False):
    errors = []
    seen = set()
    for id in ids:
        try:
            match = c.comparison.match(id)
            for mid in match.market_ids:
                if mid not in seen:
                    seen.add(mid)
                    await c.comparison.book(c.comparison.market(mid), force=force)
        except Exception as exc:
            errors.append(type(exc).__name__)
    return errors
