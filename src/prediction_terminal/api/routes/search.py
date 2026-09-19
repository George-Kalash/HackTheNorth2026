from fastapi import APIRouter, Depends, Query

from prediction_terminal.api.dependencies import container
from prediction_terminal.api.schemas import ImportRequest, SearchResponse
from prediction_terminal.bootstrap import Container

router = APIRouter()


@router.get("/search", response_model=SearchResponse)
async def search(q: str = Query(min_length=2, max_length=1000), c: Container = Depends(container)):
    return await c.search.search(q)


@router.post("/imports/venue-url", response_model=SearchResponse)
async def import_url(body: ImportRequest, c: Container = Depends(container)):
    return await c.search.import_url(body.url)
