from datetime import datetime
from decimal import Decimal

from prediction_terminal.analytics.fees import FeePolicy
from prediction_terminal.domain.markets import utcnow


def policy_for(repo, market):
    row = repo.get("ingestion_checkpoints", "fee_" + market.id)
    if not row or datetime.fromisoformat(row["expires_at"]) <= utcnow():
        return FeePolicy(market.venue, market.id)
    return FeePolicy(
        venue=market.venue,
        market_id=market.id,
        version=row["version"],
        evidence=row["evidence"],
        known=True,
        formula=row["formula"],
        rate=Decimal(row["rate"]),
        effective_at=row["reviewed_at"],
        rounding=Decimal(row["rounding"]),
    )
