from decimal import Decimal

from fastapi import APIRouter, Depends, Query

from prediction_terminal.api.dependencies import container
from prediction_terminal.api.schemas import ScannerResponse
from prediction_terminal.bootstrap import Container

router = APIRouter()


@router.get("/opportunities", response_model=ScannerResponse)
async def opportunities(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    q: str = "",
    review_state: str = "",
    classification: str = "",
    max_age: float = Query(45, gt=0),
    quantity: Decimal = Query(Decimal(10), gt=0, le=1000000),
    min_capacity: Decimal = Query(Decimal(0), ge=0),
    min_net_edge: Decimal | None = Query(None, ge=0),
    c: Container = Depends(container),
):
    return c.scanner.rows(
        limit, offset, q, review_state, classification, max_age, quantity, min_capacity, min_net_edge
    )
