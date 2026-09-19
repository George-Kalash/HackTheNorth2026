from uuid import uuid4

from fastapi import APIRouter, Depends

from prediction_terminal.api.dependencies import container
from prediction_terminal.api.schemas import AlertRequest
from prediction_terminal.bootstrap import Container

router = APIRouter()


@router.get("/alerts")
async def lists(c: Container = Depends(container)):
    return {"rules": c.repo.list("alert_rules", 100), "events": c.repo.list("alert_events", 100)}


@router.post("/alerts")
async def create(body: AlertRequest, c: Container = Depends(container)):
    if body.match_id:
        c.comparison.match(body.match_id)
    id = "rule_" + uuid4().hex
    row = {"id": id, **body.model_dump(mode="json")}
    c.repo.put("alert_rules", id, row, match_id=body.match_id)
    return row


@router.put("/alerts/{id}")
async def update(id: str, body: AlertRequest, c: Container = Depends(container)):
    if body.match_id:
        c.comparison.match(body.match_id)
    row = {"id": id, **body.model_dump(mode="json")}
    c.repo.put("alert_rules", id, row, match_id=body.match_id)
    return row


@router.delete("/alerts/{id}")
async def delete(id: str, c: Container = Depends(container)):
    c.repo.delete("alert_rules", id)
    return {"deleted": id}
