import asyncio

from fastapi import WebSocket, WebSocketDisconnect

from prediction_terminal.domain.markets import utcnow


async def gateway(ws: WebSocket, c):
    await ws.accept()
    topics: set[str] = set()
    sequence = 0

    async def send(kind, topic, data):
        nonlocal sequence
        sequence += 1
        await asyncio.wait_for(
            ws.send_json(
                {
                    "schema_version": 1,
                    "type": kind,
                    "topic": topic,
                    "sequence": sequence,
                    "sent_at": utcnow().isoformat(),
                    "data": data,
                }
            ),
            timeout=5,
        )

    try:
        await send(
            "status",
            "connection",
            {"mode": "POLLED", "message": "Browser transport connected; exchange data remains polled."},
        )
        while True:
            try:
                request = await asyncio.wait_for(ws.receive_json(), timeout=2)
                action = request.get("action")
                topic = request.get("topic", "")
                if action in {"subscribe", "resync"}:
                    if (
                        not topic.startswith(("comparison:", "book:", "opportunities:"))
                        or len(topic) > 200
                        or (topic not in topics and len(topics) >= 12)
                    ):
                        await send("error", topic, {"message": "Invalid topic or subscription limit"})
                        continue
                    if topic not in topics:
                        topics.add(topic)
                        c.subscriptions.acquire(topic)
                elif action == "unsubscribe" and topic in topics:
                    topics.remove(topic)
                    c.subscriptions.release(topic)
            except asyncio.TimeoutError:
                pass
            for topic in list(topics):
                kind, id = topic.split(":", 1)
                if kind == "book":
                    data = c.repo.latest_book(id)
                elif kind == "comparison":
                    data = {"match": c.repo.get("match_groups", id), "refresh": True}
                else:
                    data = {"refresh": True}
                # Full coalesced snapshots are sufficient; no unbounded per-client delta queue.
                await send("snapshot", topic, data)
            await send("heartbeat", "connection", {"mode": "POLLED"})
    except (WebSocketDisconnect, asyncio.TimeoutError, RuntimeError):
        pass
    finally:
        for topic in topics:
            c.subscriptions.release(topic)
