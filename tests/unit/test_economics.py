from datetime import timedelta
from decimal import Decimal as D

import pytest
from pydantic import ValidationError

from prediction_terminal.analytics.depth import breakpoints, consume, lot_floor
from prediction_terminal.analytics.fees import FeePolicy
from prediction_terminal.analytics.opportunities import simulate
from prediction_terminal.domain.markets import utcnow
from prediction_terminal.market_data.freshness import eligibility
from prediction_terminal.market_data.normalizer import complement, levels, quote


def test_complement_preserves_quantities_and_sort():
    bids = levels([[".2", "2.5"], [".7", "3.25"]], True)
    asks = complement(bids)
    assert [(a.price, a.quantity) for a in asks] == [(D(".3"), D("3.25")), (D(".8"), D("2.5"))]


def test_missing_is_not_zero(pair):
    _, books, _, _ = pair
    books[0].yes_bids = []
    assert quote(books[0]).midpoint is None
    books[0].yes_asks = []
    assert quote(books[0]).ask is None


def test_depth_vwap_partial():
    ladder = levels([[".4", "2"], [".6", "3"]])
    filled, cost, used, vwap = consume(ladder, D(4))
    assert (filled, cost, vwap) == (D(4), D(2), D(".5"))
    assert len(used) == 2
    assert consume(ladder, D(9))[0] == 5
    assert breakpoints([ladder]) == [D(2), D(5)]
    assert lot_floor(D("2.9"), D(1)) == 2


def test_spec_one_cent_conditional_floor(pair):
    markets, books, match, fees = pair
    result = simulate(match, markets, books, fees, D(1), other_costs=D(".02"))
    assert result.gross_outlay == D(".97")
    assert result.estimated_net_floor == D(".01")
    assert result.verified
    assert result.minimum_payout == 1


def test_gap_is_not_profit_and_unreviewed_has_losing_scenario(pair):
    markets, books, match, fees = pair
    match.review_state = "UNREVIEWED"
    result = simulate(match, markets, books, fees, D(1))
    assert not result.verified
    assert result.minimum_payout == 0
    assert result.estimated_net_floor == D("-.97")
    assert any("both legs lose" in s.name for s in result.scenarios)


def test_unknown_fees_and_override_never_verify(pair):
    markets, books, match, fees = pair
    fees[0] = FeePolicy("kalshi", "a")
    result = simulate(match, markets, books, fees, D(1))
    assert result.estimated_net_floor is None and not result.verified
    result = simulate(match, markets, books, fees, D(1), fee_override=D(".02"))
    assert result.estimated_net_floor == D(".01") and not result.verified


def test_stale_skew_and_insufficient_depth(pair):
    markets, books, match, fees = pair
    books[0].venue_time = utcnow() - timedelta(seconds=100)
    assert len(eligibility(books, utcnow())) >= 2
    result = simulate(match, markets, books, fees, D(101))
    assert not result.verified and result.estimated_net_floor is None
    assert not result.scenarios


def test_lot_gate_and_book_identity(pair):
    markets, books, match, fees = pair
    result = simulate(match, markets, books, fees, D(".5"))
    assert not result.verified
    assert result.book_ids == [b.id for b in books]
    assert result.rule_hashes == match.rule_hashes


def test_currency_basis_is_not_verification(pair):
    markets, books, match, fees = pair
    markets[1].settlement = markets[1].settlement.model_copy(update={"currency": "pUSD"})
    result = simulate(match, markets, books, fees, D(1), currency_basis=True)
    assert not result.verified
    assert any("denominations" in r for r in result.eligibility_reasons)


def test_fee_versions_rounding():
    a = FeePolicy("kalshi", "x", version="one", known=True, formula="quadratic", rate=D(".07"))
    b = FeePolicy("kalshi", "x", version="two", known=True, formula="quadratic", rate=D(".14"))
    ladder = levels([[".5", "10"]])
    assert a.calculate(ladder) == D(".18")
    assert b.calculate(ladder) == D(".35")


@pytest.mark.parametrize("p,q", [("NaN", "1"), ("1.1", "2"), (".5", "-1")])
def test_invalid_levels(p, q):
    with pytest.raises((ValueError, ValidationError)):
        levels([[p, q]])


def test_common_lot():
    from prediction_terminal.analytics.depth import common_lot

    assert common_lot([D(".2"), D(".3")]) == D(".6")


def test_wrong_market_fee_policy_is_not_used(pair):
    markets, books, match, fees = pair
    fees[0] = FeePolicy("kalshi", "wrong-market", known=True, formula="zero")
    result = simulate(match, markets, books, fees, D(1))
    assert not result.verified and result.estimated_net_floor is None


def test_synthetic_payoffs_and_currency_gate(pair):
    from dataclasses import replace

    from prediction_terminal.analytics.synthetic import simulate_basket
    from prediction_terminal.domain.opportunities import SimulationInputs

    markets, books, match, fees = pair
    markets.append(markets[1].model_copy(update={"id": "c"}))
    books.append(books[1].model_copy(update={"market_id": "c"}))
    fees.append(replace(fees[1], market_id="c"))
    match.market_ids.append("c")
    match.rule_hashes["c"] = markets[2].settlement.rule_hash
    match.classification = "SYNTHETIC_EQUIVALENT"
    match.replication = {"DD": [D(1), D(1), D(0)], "RD": [D(1), D(0), D(1)], "OTHER": [D(0), D(0), D(0)]}
    request = SimulationInputs(match_id=match.id, quantity=D(10))
    result = simulate_basket(match, markets, books, fees, request)
    assert result.verified and result.minimum_payout == 10
    assert result.max_size_at_threshold == 0
    assert [leg.side for leg in result.legs] == ["NO", "YES", "YES"]
    reverse = simulate_basket(match, markets, books, fees, request.model_copy(update={"reverse": True}))
    assert reverse.minimum_payout == 20
    assert reverse.max_size_at_threshold == 100
    assert [leg.side for leg in reverse.legs] == ["YES", "NO", "NO"]
    markets[2].settlement = markets[2].settlement.model_copy(update={"currency": "pUSD"})
    result = simulate_basket(match, markets, books, fees, request)
    assert not result.verified and result.minimum_payout == 0
    result = simulate_basket(match, markets, books, fees, request.model_copy(update={"currency_basis": True}))
    assert not result.verified and result.minimum_payout == 10
