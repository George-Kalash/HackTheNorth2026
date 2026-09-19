from contextlib import asynccontextmanager
from importlib import import_module
from pathlib import Path

from fastapi import FastAPI, Request, WebSocket
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from prediction_terminal.bootstrap import build
from prediction_terminal.domain.errors import TerminalError

from .streaming import gateway


def create_app(settings=None):
    @asynccontextmanager
    async def lifespan(app):
        app.state.container = build(settings)
        yield
        await app.state.container.transport.close()
        app.state.container.repo.engine.dispose()

    app = FastAPI(title="Parallax Prediction Terminal", version="1.0.0", lifespan=lifespan)

    @app.middleware("http")
    async def request_metrics(request: Request, call_next):
        import time

        from prediction_terminal.observability.logging import event

        started = time.monotonic()
        response = await call_next(request)
        elapsed = (time.monotonic() - started) * 1000
        if hasattr(request.app.state, "container"):
            request.app.state.container.metrics.counts["api_requests"] += 1
            if response.status_code >= 400:
                request.app.state.container.metrics.counts["api_errors"] += 1
        event(
            "api_request",
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            duration_ms=round(elapsed, 2),
        )
        return response

    @app.exception_handler(TerminalError)
    async def domain_error(request: Request, exc: TerminalError):
        return JSONResponse(
            status_code=exc.status, content={"error": {"code": exc.code, "message": exc.message}}
        )

    for name in [
        "search",
        "markets",
        "matches",
        "comparisons",
        "opportunities",
        "simulations",
        "watchlists",
        "alerts",
        "workspaces",
        "health",
    ]:
        app.include_router(
            import_module("prediction_terminal.api.routes." + name).router, prefix="/api/v1", tags=[name]
        )

    @app.websocket("/api/v1/stream")
    async def stream(ws: WebSocket):
        await gateway(ws, app.state.container)

    dist = Path(__file__).resolve().parents[3] / "web" / "dist"
    if dist.exists():
        app.mount("/assets", StaticFiles(directory=dist / "assets"), name="assets")

        @app.get("/{path:path}", include_in_schema=False)
        async def frontend(path: str):
            if path.startswith("api/"):
                return JSONResponse(
                    status_code=404, content={"error": {"code": "NOT_FOUND", "message": "Unknown API path"}}
                )
            return FileResponse(dist / "index.html")

    return app


app = create_app()
