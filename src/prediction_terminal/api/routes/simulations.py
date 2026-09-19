from fastapi import APIRouter, Depends

from prediction_terminal.api.dependencies import container
from prediction_terminal.api.schemas import SimulationRequest
from prediction_terminal.bootstrap import Container
from prediction_terminal.domain.opportunities import Opportunity

router = APIRouter()


@router.post("/simulations", response_model=Opportunity)
async def simulate(body: SimulationRequest, c: Container = Depends(container)):
    return await c.simulation.run(body)
