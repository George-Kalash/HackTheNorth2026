from typing import Literal

from fastapi import APIRouter, Depends

from prediction_terminal.api.dependencies import container
from prediction_terminal.api.schemas import ComparisonResponse
from prediction_terminal.bootstrap import Container

router = APIRouter()


@router.get("/comparisons/{id}", response_model=ComparisonResponse)
async def comparison(
    id: str,
    days: Literal["1", "7", "30"] = "7",
    price_type: Literal["provider", "midpoint", "bid", "ask"] = "provider",
    c: Container = Depends(container),
):
    return await c.comparison.get(id, int(days), price_type)
