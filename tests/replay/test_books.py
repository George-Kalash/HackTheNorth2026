from decimal import Decimal as D

from prediction_terminal.domain.books import BookLevel
from prediction_terminal.market_data.book_builder import BookBuilder


def test_duplicate_gap_reconnect():
    b = BookBuilder()
    b.snapshot([BookLevel(price=".5", quantity="10")], 10)
    assert b.delta(D(".5"), D(9), 11) == "APPLIED"
    assert b.delta(D(".5"), D(8), 11) == "DUPLICATE"
    assert b.levels[D(".5")] == 9
    assert b.delta(D(".5"), D(7), 13) == "GAP"
    assert not b.ready
    b.snapshot([BookLevel(price=".5", quantity="7")], 13)
    b.disconnect()
    assert not b.ready
    assert b.delta(D(".5"), D(6), 14) == "GAP"
    b.snapshot([], 14)
    assert b.ready


def test_unsequenced_requests_resnapshot():
    b = BookBuilder()
    b.snapshot([], None)
    assert b.delta(D(".2"), D(3), None) == "RESNAPSHOT"
    assert not b.ready


def test_signed_delta_quantities():
    b = BookBuilder()
    b.snapshot([BookLevel(price=".5", quantity="10")], 1)
    assert b.delta(D(".5"), D(-3), 2, absolute=False) == "APPLIED"
    assert b.levels[D(".5")] == 7
    assert b.delta(D(".5"), D(-8), 3, absolute=False) == "INVALID"
    assert not b.ready
