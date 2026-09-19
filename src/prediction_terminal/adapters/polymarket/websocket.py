"""Public events are invalidation hints; no upstream sequence guarantee is invented."""

import asyncio
import json
import random

import websockets


async def watch(tokens: list[str], dirty: asyncio.Event, metrics):
    backoff = 1
    while True:
        try:
            async with websockets.connect(
                "wss://ws-subscriptions-clob.polymarket.com/ws/market", ping_interval=20, max_size=2**22
            ) as ws:
                await ws.send(json.dumps({"assets_ids": tokens, "type": "market"}))
                metrics.counts["poly_connected"] = 1
                dirty.set()
                backoff = 1
                while True:
                    try:
                        message = await asyncio.wait_for(ws.recv(), timeout=10)
                    except asyncio.TimeoutError:
                        await ws.send("PING")
                        continue
                    if message not in {"PONG", "PING"}:
                        metrics.counts["poly_messages"] += 1
                        dirty.set()
        except asyncio.CancelledError:
            raise
        except Exception:
            metrics.counts["poly_connected"] = 0
            metrics.counts["poly_reconnects"] += 1
            dirty.set()
            await asyncio.sleep(backoff + random.random())
            backoff = min(30, backoff * 2)
