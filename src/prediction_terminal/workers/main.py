import asyncio
import signal
import time

from prediction_terminal.adapters.polymarket.websocket import watch
from prediction_terminal.bootstrap import build
from prediction_terminal.domain.markets import utcnow

from .catalog_sync import sync
from .opportunity_scan import scan
from .stream_ingest import ingest, selected_matches


async def run():
    c = build()
    stop = asyncio.Event()
    dirty = asyncio.Event()
    stream = None
    current_tokens: list[str] = []
    last_catalog = 0.0
    last_prune = 0.0
    loop = asyncio.get_running_loop()
    for sig in [signal.SIGINT, signal.SIGTERM]:
        loop.add_signal_handler(sig, stop.set)
    try:
        while not stop.is_set():
            start = time.monotonic()
            errors = []
            ids = selected_matches(c.repo)
            try:
                if start - last_catalog > 600:
                    errors += await sync(c)
                    last_catalog = start
                tokens = sorted(
                    {
                        o.token_id
                        for id in ids
                        for mid in c.comparison.match(id).market_ids
                        for o in c.comparison.market(mid).outcomes
                        if o.token_id
                    }
                )
                if tokens != current_tokens:
                    if stream:
                        stream.cancel()
                        await asyncio.gather(stream, return_exceptions=True)
                    stream = asyncio.create_task(watch(tokens, dirty, c.metrics)) if tokens else None
                    current_tokens = tokens
                changed = dirty.is_set()
                dirty.clear()
                errors += await ingest(c, ids, force=changed)
                await scan(c, ids)
                if start - last_prune > 3600:
                    c.repo.prune(c.settings.retention_days)
                    last_prune = start
            except Exception as exc:
                errors.append(type(exc).__name__)
            c.repo.put(
                "ingestion_checkpoints",
                "worker",
                {
                    "id": "worker",
                    "heartbeat": utcnow().isoformat(),
                    "mode": "POLLED",
                    "selected_matches": len(ids),
                    "public_stream_hints": bool(stream),
                    "public_stream_connected": bool(c.metrics.counts["poly_connected"]),
                    "errors": errors,
                    "cycle_seconds": time.monotonic() - start,
                },
            )
            # Invalidation hints are coalesced; refresh never exceeds the configured REST budget.
            try:
                await asyncio.wait_for(stop.wait(), timeout=c.settings.poll_seconds)
            except asyncio.TimeoutError:
                pass
    finally:
        if stream:
            stream.cancel()
            await asyncio.gather(stream, return_exceptions=True)
        await c.transport.close()
        c.repo.engine.dispose()


if __name__ == "__main__":
    asyncio.run(run())
