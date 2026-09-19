from fastapi import APIRouter, Depends
from sqlalchemy import text

from prediction_terminal.adapters.kalshi.capabilities import CAPABILITIES as K
from prediction_terminal.adapters.polymarket.capabilities import CAPABILITIES as P
from prediction_terminal.api.dependencies import container
from prediction_terminal.bootstrap import Container
from prediction_terminal.domain.markets import utcnow

router = APIRouter()


@router.get("/health/live")
async def live():
    return {"status": "ok", "time": utcnow().isoformat()}


@router.get("/health/ready")
async def ready(c: Container = Depends(container)):
    with c.repo.engine.connect() as connection:
        connection.execute(text("SELECT count(*) FROM venue_markets"))
    worker = c.repo.get("ingestion_checkpoints", "worker")
    return {
        "status": "ready",
        "venues": [K, P],
        "worker": worker,
        "metrics": c.metrics.snapshot(),
        "thresholds": {
            "max_age_seconds": c.settings.max_age_seconds,
            "max_skew_seconds": c.settings.max_skew_seconds,
            "poll_seconds": c.settings.poll_seconds,
        },
    }
