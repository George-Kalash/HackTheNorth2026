from datetime import datetime, timedelta, timezone

import httpx
import pytest
from fastapi.testclient import TestClient

from marketlens.app import app, identifier
from marketlens.clients.http import PublicHTTP, SourceError
from marketlens.clients.kalshi import dollars
from marketlens.clients.kalshi import normalize as kalshi_normalize
from marketlens.clients.polymarket import Polymarket
from marketlens.clients.polymarket import normalize as poly_normalize
from marketlens.matching import candidates, fed_bucket
from marketlens.models import Market, price
from marketlens.opportunities import compare


def market(platform="Kalshi", **kwargs):
    return Market(
        platform=platform,
        id=platform,
        event_id="event",
        title="Fed decision October 2026",
        outcome="No change",
        url="https://example.com",
        active=True,
        **kwargs,
    )


def test_price_units_and_missing():
    assert dollars({"yes_ask_dollars": "0.1250", "yes_ask": 50}, "yes_ask") == 0.125
    assert dollars({"yes_ask": 50}, "yes_ask") == 0.5
    assert dollars({}, "yes_ask") is None
    assert price("0") == 0
    assert price("NaN") is None
    assert price("1.2") is None


def test_poly_outcome_order():
    m = poly_normalize(
        {
            "id": "1",
            "question": "Test?",
            "outcomes": '["No", "Yes"]',
            "outcomePrices": '["0.7", "0.3"]',
            "clobTokenIds": '["no", "yes"]',
        },
        {"slug": "test"},
    )
    assert m.probability == 0.3
    assert m.token_yes == "yes"
    assert m.token_no == "no"
    assert m.no_ask is None


def test_kalshi_zero_midpoint_fallback():
    m = kalshi_normalize(
        {
            "ticker": "KX-T",
            "title": "Test",
            "yes_bid_dollars": "0",
            "yes_ask_dollars": ".01",
            "last_price_dollars": ".02",
        },
        {"series_ticker": "KX", "event_ticker": "KX-E"},
    )
    assert m.probability == 0.02
    assert "Last trade" in m.probability_basis


def test_edge_uses_asks_not_indicated_probability():
    k = market(probability=0.4, yes_ask=0.45, no_ask=0.62)
    p = market("Polymarket", probability=0.6, yes_ask=0.63, no_ask=0.41)
    result = compare(k, p, 0.02)
    best = result["trades"][0]
    assert result["gap_pp"] == -20
    assert best["cost"] == 0.86
    assert best["adjusted_edge"] == 0.12
    assert best["yes_platform"] == "Kalshi"
    assert best["max_pairs_at_top"] is None


def test_missing_closed_and_stale_quotes():
    assert compare(market(), market("Polymarket"))["trades"] == []
    k = market(yes_ask=0.4, no_ask=0.6)
    p = market(
        "Polymarket",
        yes_ask=0.5,
        no_ask=0.5,
        quote_time=(datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat(),
    )
    assert compare(k, p)["trades"][0]["stale"]
    p.active = False
    assert compare(k, p)["trades"] == []


def test_matching_rejects_opposite_fed_buckets():
    k, p = market(), market("Polymarket")
    k.outcome, p.outcome = "Cut 25bps", "25 bps increase"
    assert fed_bucket(k) == "cut_25"
    assert candidates([k], [p]) == []
    p.outcome = "25 bps decrease"
    assert candidates([k], [p])[0]["equivalence"] == "unverified"
    p.outcome = "50+ bps decrease"
    assert fed_bucket(p) == "cut_large"


def test_urls_cannot_redirect_backend():
    assert (
        identifier(
            "https://kalshi.com/markets/kxfeddecision/fed-meeting/kxfeddecision-26oct", "Kalshi"
        )
        == "KXFEDDECISION-26OCT"
    )
    assert identifier("https://polymarket.com/event/test?x=1", "Polymarket") == "test"
    from fastapi import HTTPException

    with pytest.raises(HTTPException):
        identifier("https://localhost/private", "Kalshi")


async def test_orderbooks_unsorted_and_missing_sides():
    class HTTP:
        async def get(self, base, path, params, **kwargs):
            if params["token_id"] == "yes":
                return {
                    "asks": [{"price": ".6", "size": "5"}, {"price": ".4", "size": "3"}],
                    "bids": [{"price": ".3", "size": "5"}],
                }
            return {"asks": [], "bids": []}

    m = market("Polymarket", token_yes="yes", token_no="no")
    m = await Polymarket(HTTP()).refresh(m)
    assert m.yes_ask == 0.4
    assert m.probability == 0.35
    assert m.no_ask is None


async def test_http_error_and_cache():
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(200, json={"ok": True})

    h = PublicHTTP()
    await h.client.aclose()
    h.client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    await h.get("https://test", "/data")
    await h.get("https://test", "/data")
    assert len(calls) == 1
    await h.close()
    h.client = httpx.AsyncClient(transport=httpx.MockTransport(lambda _: httpx.Response(403)))
    with pytest.raises(SourceError):
        await h.get("https://test", "/denied")
    await h.close()


def test_app_shell_and_validation():
    with TestClient(app) as client:
        assert client.get("/").status_code == 200
        assert client.get("/static/app.js").status_code == 200
        assert client.get("/api/health").json() == {"status": "ok"}
        assert client.post("/api/compare", json={}).status_code == 422


def test_kalshi_empty_bid_is_not_a_one_dollar_ask():
    m = kalshi_normalize(
        {
            "ticker": "KX-T",
            "title": "Test",
            "yes_bid_dollars": "0",
            "no_ask_dollars": "1",
            "yes_bid_size_fp": "0",
        },
        {"series_ticker": "KX", "event_ticker": "KX-E"},
    )
    assert m.no_ask is None


async def test_series_search_prioritizes_subject_over_event_month():
    class HTTP:
        async def get(self, base, path, params=None, **kwargs):
            if path == "/series":
                return {
                    "series": [{"ticker": "KXFEDDECISION", "title": "Fed meeting"}]
                    + [
                        {"ticker": f"OTHER{i}", "title": "October interest rate decision"}
                        for i in range(8)
                    ]
                }
            return {
                "events": [
                    {
                        "event_ticker": params["series_ticker"] + "-26OCT",
                        "title": "Fed decision October 2026",
                    }
                ]
            }

    from marketlens.clients.kalshi import Kalshi

    events = await Kalshi(HTTP()).search("Fed decision October 2026")
    assert any(e.id == "KXFEDDECISION-26OCT" for e in events)
