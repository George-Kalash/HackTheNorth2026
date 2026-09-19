from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, Query

from prediction_terminal.api.dependencies import container
from prediction_terminal.api.schemas import FeePolicyRequest
from prediction_terminal.bootstrap import Container
from prediction_terminal.domain.books import BookSnapshot
from prediction_terminal.domain.history import PriceHistory, PriceType
from prediction_terminal.domain.markets import VenueMarket

router = APIRouter()


@router.get("/markets/{id}", response_model=VenueMarket)
async def market(id: str, c: Container = Depends(container)):
    return c.comparison.market(id)


@router.get("/markets/{id}/book", response_model=BookSnapshot)
async def book(id: str, c: Container = Depends(container)):
    return await c.comparison.book(c.comparison.market(id))


@router.get("/markets/{id}/history", response_model=PriceHistory)
async def history(
    id: str,
    price_type: PriceType = "midpoint",
    days: Literal["1", "7", "30"] = "7",
    from_: datetime | None = Query(None, alias="from"),
    to: datetime | None = Query(None),
    interval: Literal["1m", "1h", "1d"] | None = None,
    c: Container = Depends(container),
):
    return await c.comparison.history_range(
        c.comparison.market(id), price_type, int(days), from_, to, interval
    )


@router.get("/markets/{id}/fee-policy")
async def get_fee_policy(id: str, c: Container = Depends(container)):
    c.comparison.market(id)
    return c.repo.get("ingestion_checkpoints", "fee_" + id) or {"status": "UNKNOWN"}


@router.post("/markets/{id}/fee-policy")
async def save_fee_policy(id: str, body: "FeePolicyRequest", c: Container = Depends(container)):
    from datetime import datetime
    from uuid import uuid4

    from prediction_terminal.domain.errors import TerminalError
    from prediction_terminal.domain.markets import utcnow

    c.comparison.market(id)
    try:
        expires = datetime.fromisoformat(body.expires_at)
    except ValueError as exc:
        raise TerminalError("INVALID_EXPIRY", "Use a UTC ISO expiry", 422) from exc
    if expires.tzinfo is None or not 0 < (expires - utcnow()).total_seconds() <= 86400 * 31:
        raise TerminalError("INVALID_EXPIRY", "Fee evidence expires between now and 31 days from now", 422)
    row = {
        "id": "fee_" + id,
        "market_id": id,
        "version": "reviewed_" + uuid4().hex,
        "reviewed_at": utcnow().isoformat(),
        **body.model_dump(mode="json"),
    }
    c.repo.put("ingestion_checkpoints", row["id"], row)
    c.repo.put("raw_inputs", row["version"], row)
    return row


@router.get("/markets", response_model=list[VenueMarket])
async def list_markets(
    limit: int = Query(100, ge=1, le=1000), offset: int = Query(0, ge=0), c: Container = Depends(container)
):
    return c.repo.list("venue_markets", limit, offset)
