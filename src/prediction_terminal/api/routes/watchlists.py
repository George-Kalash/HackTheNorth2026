from fastapi import APIRouter, Depends

from prediction_terminal.api.dependencies import container
from prediction_terminal.api.schemas import WatchlistRequest
from prediction_terminal.bootstrap import Container

router = APIRouter()


@router.get("/watchlists")
async def lists(c: Container = Depends(container)):
    return c.repo.list("watchlists", 100)


@router.post("/watchlists")
async def create(body: WatchlistRequest, c: Container = Depends(container)):
    return c.watchlists.save(None, body.name, body.match_ids)


@router.put("/watchlists/{id}")
async def update(id: str, body: WatchlistRequest, c: Container = Depends(container)):
    return c.watchlists.save(id, body.name, body.match_ids)


@router.delete("/watchlists/{id}")
async def delete(id: str, c: Container = Depends(container)):
    c.repo.delete("watchlists", id)
    return {"deleted": id}
