from decimal import Decimal

import pytest

from prediction_terminal.analytics.fees import FeePolicy
from prediction_terminal.domain.books import BookLevel, BookSnapshot
from prediction_terminal.domain.markets import Outcome, SettlementSpec, VenueMarket, utcnow
from prediction_terminal.domain.matches import MatchGroup


@pytest.fixture
def pair():
    """FICTIONAL deterministic contracts; never loaded into the live terminal."""
    spec = SettlementSpec(rule_text="Fictional identical rule", rule_hash="fictional-rule-v1", currency="USD")
    markets = [
        VenueMarket(
            id="a",
            venue="kalshi",
            external_id="A",
            event_id="event-a",
            title="Fictional event",
            outcome="Same proposition",
            source_url="https://example.invalid",
            active=True,
            outcomes=[Outcome(name="YES"), Outcome(name="NO")],
            settlement=spec,
            lot_size=Decimal(1),
        ),
        VenueMarket(
            id="b",
            venue="polymarket",
            external_id="B",
            event_id="event-b",
            title="Fictional event",
            outcome="Same proposition",
            source_url="https://example.invalid",
            active=True,
            outcomes=[Outcome(name="YES"), Outcome(name="NO")],
            settlement=spec,
            lot_size=Decimal(1),
        ),
    ]

    def level(p, q=100):
        return BookLevel(price=Decimal(p), quantity=Decimal(q))

    books = [
        BookSnapshot(
            market_id="a",
            yes_bids=[level(".53")],
            yes_asks=[level(".54")],
            no_bids=[level(".45")],
            no_asks=[level(".47")],
            lot_size=Decimal(1),
            venue_time=utcnow(),
        ),
        BookSnapshot(
            market_id="b",
            yes_bids=[level(".55")],
            yes_asks=[level(".57")],
            no_bids=[level(".42")],
            no_asks=[level(".43")],
            lot_size=Decimal(1),
            venue_time=utcnow(),
        ),
    ]
    match = MatchGroup(
        id="match-fictional",
        title="FICTIONAL pair",
        market_ids=["a", "b"],
        classification="EXACT",
        review_state="APPROVED",
        score=1,
        reasons=[],
        differences=[],
        rule_hashes={"a": "fictional-rule-v1", "b": "fictional-rule-v1"},
    )
    fees = [
        FeePolicy(
            m.venue,
            m.id,
            version="fictional-zero",
            known=True,
            formula="zero",
            evidence="Synthetic test only",
        )
        for m in markets
    ]
    return markets, books, match, fees
