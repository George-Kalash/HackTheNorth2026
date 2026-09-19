from prediction_terminal.domain.errors import TerminalError


def save(repo, id, payload):
    if payload.get("schema_version") != 1:
        raise TerminalError("WORKSPACE_VERSION", "Unsupported workspace schema version", 422)
    row = {"id": id, **payload}
    repo.put("workspaces", id, row)
    return row
