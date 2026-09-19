import httpx
import pytest

from prediction_terminal.adapters.common.transport import Transport
from prediction_terminal.config import Settings
from prediction_terminal.domain.errors import SourceUnavailable
from prediction_terminal.observability.metrics import Metrics


class Archive:
    def record(self, source, data):
        return "test"


async def test_retry_after_and_no_redirects():
    calls = []

    def handler(request):
        calls.append(request)
        return (
            httpx.Response(429, headers={"Retry-After": "0"})
            if len(calls) == 1
            else httpx.Response(200, json={"ok": True})
        )

    transport = Transport(Settings(requests_per_second=20), Archive(), Metrics())
    await transport.client.aclose()
    transport.client = httpx.AsyncClient(transport=httpx.MockTransport(handler), follow_redirects=False)
    assert await transport.get("https://clob.polymarket.com", "/book") == {"ok": True}
    assert len(calls) == 2
    await transport.close()
    transport.client = httpx.AsyncClient(
        transport=httpx.MockTransport(
            lambda _: httpx.Response(302, headers={"Location": "http://127.0.0.1/private"})
        ),
        follow_redirects=False,
    )
    with pytest.raises(SourceUnavailable):
        await transport.get("https://clob.polymarket.com", "/book")
    await transport.close()


async def test_unapproved_origin_rejected():
    transport = Transport(Settings(), Archive(), Metrics())
    try:
        with pytest.raises(SourceUnavailable):
            await transport.get("http://localhost", "/private")
    finally:
        await transport.close()
