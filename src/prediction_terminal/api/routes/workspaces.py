from fastapi import APIRouter, Depends

from prediction_terminal.api.dependencies import container
from prediction_terminal.api.schemas import WorkspaceRequest
from prediction_terminal.application.workspaces import save
from prediction_terminal.bootstrap import Container

router = APIRouter()


@router.get("/workspaces")
async def lists(c: Container = Depends(container)):
    return c.repo.list("workspaces", 100)


@router.get("/workspaces/{id}")
async def get(id: str, c: Container = Depends(container)):
    from prediction_terminal.domain.errors import TerminalError

    row = c.repo.get("workspaces", id)
    if not row:
        raise TerminalError("NOT_FOUND", "Workspace not found", 404)
    return row


@router.put("/workspaces/{id}")
async def update(id: str, body: WorkspaceRequest, c: Container = Depends(container)):
    return save(c.repo, id, body.model_dump(mode="json"))


@router.delete("/workspaces/{id}")
async def delete(id: str, c: Container = Depends(container)):
    c.repo.delete("workspaces", id)
    return {"deleted": id}
