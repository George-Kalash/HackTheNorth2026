import json
from pathlib import Path

from prediction_terminal.adapters.kalshi.mapper import book as kalshi_book
from prediction_terminal.adapters.kalshi.mapper import event as kalshi_event
from prediction_terminal.adapters.polymarket.mapper import event as poly_event
from prediction_terminal.market_data.normalizer import quote


def fixture(name):
    return json.loads(Path("tests/fixtures/recorded", name + ".json").read_text())["data"]


def test_recorded_kalshi_contract():
    e = kalshi_event(fixture("kalshi_event"))
    assert len(e.markets) == 5
    b = kalshi_book(fixture("kalshi_book"), e.markets[2])
    assert b.yes_asks and b.no_asks
    assert quote(b).midpoint is not None
    assert all(a.quantity > 0 for a in b.yes_asks)


def test_recorded_polymarket_named_tokens():
    raw = fixture("poly_event")[0]
    e = poly_event(raw)
    assert len(e.markets) == 5
    m = raw["markets"][0]
    original = dict(m)
    for key in ["outcomes", "clobTokenIds", "outcomePrices"]:
        m[key] = json.dumps(list(reversed(json.loads(m[key]))))
    reversed_event = poly_event(raw)
    before = {o.name: o.token_id for o in e.markets[0].outcomes}
    after = {o.name: o.token_id for o in reversed_event.markets[0].outcomes}
    assert before == after
    assert e.markets[0].indicative == reversed_event.markets[0].indicative
    m.update(original)
