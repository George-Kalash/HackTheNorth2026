from uuid import uuid4

from fastapi import APIRouter, Depends

from prediction_terminal.api.dependencies import container
from prediction_terminal.api.schemas import SyntheticMappingRequest
from prediction_terminal.bootstrap import Container
from prediction_terminal.domain.matches import MatchGroup, ReviewRecord
from prediction_terminal.matching.review import review

router = APIRouter()


@router.get("/matches/{id}", response_model=MatchGroup)
async def get_match(id: str, c: Container = Depends(container)):
    return c.comparison.match(id)


@router.post("/matches/{id}/review", response_model=MatchGroup)
async def review_match(id: str, body: ReviewRecord, c: Container = Depends(container)):
    from prediction_terminal.domain.errors import TerminalError

    if body.match_id != id:
        raise TerminalError("MATCH_ID_CONFLICT", "Review match ID differs from route", 422)
    match = review(c.comparison.match(id), body)
    c.repo.put("match_groups", id, match.model_dump(mode="json"))
    c.repo.put("match_reviews", "review_" + uuid4().hex, body.model_dump(mode="json"), match_id=id)
    return match


@router.get("/matches/{id}/reviews")
async def reviews(id: str, c: Container = Depends(container)):
    return [r for r in c.repo.list("match_reviews", 1000) if r["match_id"] == id]


@router.post("/matches/synthetic", response_model=MatchGroup)
async def synthetic(body: SyntheticMappingRequest, c: Container = Depends(container)):
    from prediction_terminal.application.synthetic import create_mapping

    return create_mapping(c, body)
