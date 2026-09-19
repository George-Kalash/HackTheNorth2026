import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient

from prediction_terminal.api.app import create_app
from prediction_terminal.application.search import parse_url
from prediction_terminal.config import Settings
from prediction_terminal.domain.errors import TerminalError
from prediction_terminal.domain.markets import Event
from prediction_terminal.market_data.catalog import store_event


@pytest.fixture
def client(tmp_path, monkeypatch, pair):
    url = "sqlite:///" + str(tmp_path / "test.db")
    monkeypatch.setenv("PT_DATABASE_URL", url)
    command.upgrade(Config("alembic.ini"), "head")
    with TestClient(create_app(Settings(database_url=url))) as c:
        repo = c.app.state.container.repo
        markets, books, match, _ = pair
        for m, b in zip(markets, books):
            store_event(
                repo,
                Event(
                    id=m.event_id,
                    venue=m.venue,
                    external_id=m.event_id,
                    title="Fictional",
                    source_url=m.source_url,
                    markets=[m],
                ),
            )
            repo.put("book_snapshots", b.id, b.model_dump(mode="json"), market_id=m.id)
        repo.put("match_groups", match.id, match.model_dump(mode="json"))
        yield c


def test_migrations_health_workspace_watchlist(client):
    assert client.get("/api/v1/health/ready").status_code == 200
    assert (
        client.post(
            "/api/v1/watchlists", json={"name": "Research", "match_ids": ["match-fictional"]}
        ).status_code
        == 200
    )
    assert client.get("/api/v1/watchlists").json()[0]["match_ids"] == ["match-fictional"]
    payload = {
        "schema_version": 1,
        "name": "Compare",
        "state": {"selected": {"A": "match-fictional"}, "leftWidth": 280},
    }
    assert client.put("/api/v1/workspaces/local", json=payload).status_code == 200
    assert client.get("/api/v1/workspaces/local").json()["state"]["leftWidth"] == 280
    assert client.put("/api/v1/workspaces/local", json={**payload, "schema_version": 2}).status_code == 422


def test_simulation_validation_unknown_fees(client):
    assert (
        client.post("/api/v1/simulations", json={"match_id": "match-fictional", "quantity": -1}).status_code
        == 422
    )
    r = client.post("/api/v1/simulations", json={"match_id": "match-fictional", "quantity": "1"})
    assert r.status_code == 200
    assert not r.json()["verified"] and r.json()["estimated_net_floor"] is None
    assert client.get("/api/v1/opportunities").json()["items"][0]["verified"] is False


def test_review_change_invalidates_and_is_audited(client, pair):
    c = client.app.state.container
    market = pair[0][0].model_copy(deep=True)
    market.settlement.rule_hash = "changed"
    market.settlement.rule_text = "Amended fictional rules"
    store_event(
        c.repo,
        Event(
            id=market.event_id,
            venue=market.venue,
            external_id=market.event_id,
            title="Fictional",
            source_url=market.source_url,
            markets=[market],
        ),
    )
    assert c.repo.get("match_groups", "match-fictional")["review_state"] == "REVOKED"
    assert client.get("/api/v1/matches/match-fictional/reviews").json()


def test_websocket_envelopes(client):
    with client.websocket_connect("/api/v1/stream") as ws:
        first = ws.receive_json()
        assert first["type"] == "status" and first["schema_version"] == 1
        ws.send_json({"action": "subscribe", "topic": "comparison:match-fictional"})
        second = ws.receive_json()
        assert second["type"] == "snapshot" and second["sequence"] > first["sequence"]
        ws.send_json({"action": "unsubscribe", "topic": "comparison:match-fictional"})


@pytest.mark.parametrize(
    "url",
    [
        "http://kalshi.com/markets/a/b/c",
        "https://evil.com/event/x",
        "https://kalshi.com.evil.com/markets/a/b",
        "https://user:pass@polymarket.com/event/test",
        "https://polymarket.com:9000/event/test",
        "https://polymarket.com/event/../private",
        "https://127.0.0.1/event/x",
    ],
)
def test_ssrf_import_boundary(url):
    with pytest.raises(TerminalError):
        parse_url(url)


def test_no_order_routes(client):
    paths = client.get("/openapi.json").json()["paths"]
    assert not any(any(word in p for word in ["orders", "sign", "deposit", "wallet"]) for p in paths)


def test_comparison_accepts_string_query_days(client, monkeypatch):
    async def fake_history(market, price_type, days):
        from prediction_terminal.domain.history import PriceHistory

        return PriceHistory(
            market_id=market.id, price_type=price_type, source="fictional", points=[], interval_seconds=60
        )

    monkeypatch.setattr(client.app.state.container.comparison, "history", fake_history)
    assert client.get("/api/v1/comparisons/match-fictional?days=7&price_type=provider").status_code == 200
    assert client.get("/api/v1/comparisons/match-fictional?days=99").status_code == 422


def test_fee_policy_requires_evidence_and_versions(client):
    from datetime import timedelta

    from prediction_terminal.domain.markets import utcnow

    body = {
        "formula": "zero",
        "rate": "0",
        "evidence": "Fictional test evidence: verified market and date fee schedule; not a live fee claim.",
        "expires_at": (utcnow() + timedelta(days=1)).isoformat(),
    }
    first = client.post("/api/v1/markets/a/fee-policy", json=body)
    assert first.status_code == 200
    second = client.post("/api/v1/markets/a/fee-policy", json=body)
    assert first.json()["version"] != second.json()["version"]
    assert (
        client.post("/api/v1/markets/a/fee-policy", json={**body, "evidence": "unknown"}).status_code == 422
    )
    assert (
        client.post(
            "/api/v1/markets/a/fee-policy", json={**body, "expires_at": "2000-01-01T00:00:00Z"}
        ).status_code
        == 422
    )


def test_synthetic_overlap_rejected(client, pair):
    # Add a third fictional Polymarket outcome before constructing a basket.
    c = client.app.state.container
    third = pair[0][1].model_copy(deep=True)
    third.id = "c"
    third.external_id = "C"
    store_event(
        c.repo,
        Event(
            id=third.event_id,
            venue=third.venue,
            external_id=third.event_id,
            title="Fictional",
            source_url=third.source_url,
            markets=[third],
        ),
    )
    payload = {
        "name": "Fictional Senate basket",
        "target_market_id": "a",
        "basket_market_ids": ["b", "c"],
        "scenario_yes_payouts": {"DD": ["1", "1", "1"], "RD": ["1", "0", "1"], "OTHER": ["0", "0", "0"]},
        "coverage_evidence": "Fictional scenario universe for a deterministic regression test.",
    }
    assert client.post("/api/v1/matches/synthetic", json=payload).status_code == 422
    payload["scenario_yes_payouts"]["DD"] = ["1", "1", "0"]
    r = client.post("/api/v1/matches/synthetic", json=payload)
    assert r.status_code == 200 and r.json()["review_state"] == "UNREVIEWED"


def test_unknown_budget_fees_are_blocked(client):
    r = client.post("/api/v1/simulations", json={"match_id": "match-fictional", "budget": "10"})
    assert r.status_code == 422
    r = client.post(
        "/api/v1/simulations", json={"match_id": "match-fictional", "budget": "10", "manual_total_fees": "0"}
    )
    assert r.status_code == 200 and not r.json()["verified"]
    assert float(r.json()["gross_outlay"]) <= 10


def test_removed_market_lifecycle(client, pair):
    repo = client.app.state.container.repo
    m = pair[0][0]
    store_event(
        repo,
        Event(
            id=m.event_id,
            venue=m.venue,
            external_id=m.event_id,
            title="Fictional",
            source_url=m.source_url,
            markets=[],
        ),
    )
    assert repo.get("venue_markets", m.id)["active"] is False


def test_synthetic_budget_and_scanner(client, pair):
    from decimal import Decimal

    repo = client.app.state.container.repo
    markets, books, match, _ = pair
    third = markets[1].model_copy(update={"id": "c", "external_id": "C"})
    store_event(
        repo,
        Event(
            id=third.event_id,
            venue=third.venue,
            external_id=third.event_id,
            title="Fictional",
            source_url=third.source_url,
            markets=[markets[1], third],
        ),
    )
    book = books[1].model_copy(update={"id": "book-c", "market_id": "c"})
    repo.put("book_snapshots", book.id, book.model_dump(mode="json"), market_id="c")
    match.market_ids.append("c")
    match.rule_hashes["c"] = third.settlement.rule_hash
    match.classification = "SYNTHETIC_EQUIVALENT"
    match.replication = {
        "DD": [Decimal(1), Decimal(1), Decimal(0)],
        "RD": [Decimal(1), Decimal(0), Decimal(1)],
        "OTHER": [Decimal(0), Decimal(0), Decimal(0)],
    }
    repo.put("match_groups", match.id, match.model_dump(mode="json"))
    assert client.post("/api/v1/simulations", json={"match_id": match.id, "budget": "10"}).status_code == 422
    for reverse in [False, True]:
        response = client.post(
            "/api/v1/simulations",
            json={"match_id": match.id, "budget": "10", "manual_total_fees": "0", "reverse": reverse},
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert Decimal(data["gross_outlay"]) <= 10
        assert len(data["legs"]) == 3 and not data["verified"]
        assert Decimal(data["quantity"]) == (Decimal(7) if reverse else Decimal(6))
    assert len(client.get("/api/v1/opportunities").json()["items"][0]["proposed_legs"]) == 3


@pytest.mark.parametrize(
    "state",
    [
        {"selected": None},
        {"ranges": {"A": 99}},
        {"leftWidth": -1},
        {"set": "untrusted"},
        {"scannerFilters": {"verified": "true"}},
    ],
)
def test_workspace_rejects_malformed_state(client, state):
    assert client.put("/api/v1/workspaces/bad", json={"schema_version": 1, "state": state}).status_code == 422
