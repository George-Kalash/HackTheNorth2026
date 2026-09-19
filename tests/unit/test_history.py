from datetime import timedelta

from prediction_terminal.domain.history import PriceHistory, PricePoint
from prediction_terminal.domain.markets import utcnow
from prediction_terminal.market_data.history import align


def test_no_mixed_type_overlay():
    a = PriceHistory(
        market_id="a", price_type="last_trade", source="fictional", points=[], interval_seconds=60
    )
    b = a.model_copy(update={"market_id": "b", "price_type": "indicative"})
    assert align(a, b)[1]


def test_bounded_asof_no_future_leak():
    now = utcnow()
    a = PriceHistory(
        market_id="a",
        price_type="midpoint",
        source="fictional",
        points=[PricePoint(time=now, price=".5")],
        interval_seconds=60,
    )
    b = a.model_copy(
        update={"market_id": "b", "points": [PricePoint(time=now + timedelta(seconds=1), price=".4")]}
    )
    assert align(a, b)[0][0]["right"] is None
    b.points = [PricePoint(time=now - timedelta(seconds=60), price=".4")]
    assert align(a, b)[0][0]["spread_pp"] == "10.0"
    b.points = [PricePoint(time=now - timedelta(seconds=121), price=".4")]
    assert align(a, b)[0][0]["right"] is None


def test_basket_history_requires_every_component_and_never_uses_future():
    from datetime import timedelta
    from decimal import Decimal

    from prediction_terminal.domain.history import PriceHistory, PricePoint
    from prediction_terminal.domain.markets import utcnow
    from prediction_terminal.market_data.history import align_basket

    t = utcnow()

    def history(id, points):
        return PriceHistory(
            market_id=id,
            price_type="midpoint",
            source="fictional",
            interval_seconds=60,
            points=[PricePoint(time=time, price=price) for time, price in points],
        )

    target = history("target", [(t, Decimal(".6")), (t + timedelta(seconds=300), Decimal(".6"))])
    a = history("a", [(t - timedelta(seconds=10), Decimal(".2"))])
    b = history("b", [(t - timedelta(seconds=5), Decimal(".3"))])
    rows, _ = align_basket([target, a, b])
    assert Decimal(rows[0]["spread_pp"]) == 10
    assert rows[1]["spread_pp"] is None
    b.points[0].time = t + timedelta(seconds=1)
    assert align_basket([target, a, b])[0][0]["spread_pp"] is None
    b.price_type = "last_trade"
    assert align_basket([target, a, b])[0] == []
