import asyncio
import re
from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import urlparse

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from marketlens.clients.http import PublicHTTP, SourceError
from marketlens.clients.kalshi import Kalshi
from marketlens.clients.polymarket import Polymarket
from marketlens.matching import candidates
from marketlens.models import now
from marketlens.opportunities import compare

STATIC = Path(__file__).parent / "static"


@asynccontextmanager
async def lifespan(app):
    app.state.http = PublicHTTP()
    app.state.kalshi = Kalshi(app.state.http)
    app.state.polymarket = Polymarket(app.state.http)
    yield
    await app.state.http.close()


app = FastAPI(title="MarketLens", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=STATIC), name="static")


def identifier(value, platform):
    value = value.strip()
    if "://" in value:
        url = urlparse(value)
        allowed = (
            {"kalshi.com", "www.kalshi.com"}
            if platform == "Kalshi"
            else {"polymarket.com", "www.polymarket.com"}
        )
        if url.hostname not in allowed:
            raise HTTPException(422, f"Expected a {platform} URL")
        parts = url.path.strip("/").split("/")
        value = (
            parts[-1]
            if platform == "Kalshi"
            else parts[1]
            if len(parts) > 1 and parts[0] == "event"
            else ""
        )
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,250}", value):
        raise HTTPException(422, "Use an event URL, Kalshi event ticker, or Polymarket event slug.")
    return value.upper() if platform == "Kalshi" else value


async def safe(call):
    try:
        return await call, None
    except SourceError as exc:
        return None, str(exc)


@app.get("/")
async def index():
    return FileResponse(STATIC / "index.html")


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.get("/api/search")
async def search(q: str = Query(min_length=2, max_length=250)):
    async def lookup():
        if "://" in q or q.upper().startswith("KX"):
            platform = "Polymarket" if "polymarket.com" in q else "Kalshi"
            client = app.state.polymarket if platform == "Polymarket" else app.state.kalshi
            e = await client.event(identifier(q, platform))
            other = app.state.kalshi if platform == "Polymarket" else app.state.polymarket
            found, error = await safe(other.search(e.title))
            return {"events": [e] + (found or []), "errors": [error] if error else []}
        responses = await asyncio.gather(
            safe(app.state.kalshi.search(q)), safe(app.state.polymarket.search(q))
        )
        return {
            "events": [e for items, _ in responses for e in items or []],
            "errors": [error for _, error in responses if error],
        }

    try:
        result = await lookup()
    except SourceError as exc:
        raise HTTPException(502, str(exc)) from exc
    return {
        **result,
        "coverage": "Kalshi: top 6 matching series, up to 600 open events each. Polymarket: first 20 search events. Results are not exhaustive.",
    }


class EventsRequest(BaseModel):
    kalshi: str = Field(min_length=1, max_length=500)
    polymarket: str = Field(min_length=1, max_length=500)


class CompareRequest(EventsRequest):
    kalshi_market: str = Field(max_length=250)
    polymarket_market: str = Field(max_length=250)
    days: int = Field(default=7)
    allowance: float = Field(default=0, ge=0, le=1, allow_inf_nan=False)


async def get_events(body):
    return await asyncio.gather(
        safe(app.state.kalshi.event(identifier(body.kalshi, "Kalshi"))),
        safe(app.state.polymarket.event(identifier(body.polymarket, "Polymarket"))),
    )


@app.post("/api/events")
async def events(body: EventsRequest):
    (k, ke), (p, pe) = await get_events(body)
    return {
        "kalshi": k,
        "polymarket": p,
        "errors": [e for e in [ke, pe] if e],
        "candidates": candidates(k.markets, p.markets) if k and p else [],
        "fetched_at": now(),
    }


@app.post("/api/compare")
async def comparison(body: CompareRequest):
    if body.days not in {1, 7, 30}:
        raise HTTPException(422, "History range must be 1, 7 or 30 days")
    (ke, kerr), (pe, perr) = await get_events(body)
    if kerr or perr:
        raise HTTPException(502, " | ".join(filter(None, [kerr, perr])))
    k = next((m for m in ke.markets if m.id == body.kalshi_market), None)
    p = next((m for m in pe.markets if m.id == body.polymarket_market), None)
    if not k or not p:
        raise HTTPException(404, "Selected contract does not belong to this event")
    k, p = await asyncio.gather(app.state.kalshi.refresh(k), app.state.polymarket.refresh(p))
    (kh, kherr), (ph, pherr) = await asyncio.gather(
        safe(app.state.kalshi.history(k, body.days)),
        safe(app.state.polymarket.history(p, body.days)),
    )
    return {
        "kalshi": k,
        "polymarket": p,
        **compare(k, p, body.allowance),
        "history": {"Kalshi": kh or [], "Polymarket": ph or []},
        "errors": [e for e in [kherr, pherr] if e],
        "fetched_at": now(),
    }
