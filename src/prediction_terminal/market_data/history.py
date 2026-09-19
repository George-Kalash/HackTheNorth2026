from datetime import timedelta

from prediction_terminal.domain.history import PriceHistory


def align(left: PriceHistory, right: PriceHistory, max_age_seconds: int = 120):
    """Only like-for-like price types; bounded backward as-of alignment, no future leakage."""
    if left.price_type != right.price_type:
        return [], ["Price types differ; overlay and historical spread are disabled."]
    points = sorted(right.points, key=lambda p: p.time)
    index = 0
    rows: list[dict[str, str | None]] = []
    for a in sorted(left.points, key=lambda p: p.time):
        while index + 1 < len(points) and points[index + 1].time <= a.time:
            index += 1
        b = points[index] if points else None
        if b and timedelta(0) <= a.time - b.time <= timedelta(seconds=max_age_seconds):
            rows.append(
                {
                    "time": a.time.isoformat(),
                    "left": str(a.price),
                    "right": str(b.price),
                    "spread_pp": str((a.price - b.price) * 100),
                }
            )
        else:
            rows.append({"time": a.time.isoformat(), "left": str(a.price), "right": None, "spread_pp": None})
    return rows, []


def align_basket(histories: list[PriceHistory], max_age_seconds: int = 120):
    """Target minus sum of component YES prices; never label the sum a probability."""
    if len(histories) < 3:
        return [], ["A basket requires a target and at least two components."]
    if len({h.price_type for h in histories}) != 1:
        return [], ["Price types differ; synthetic historical spread is disabled."]
    from decimal import Decimal

    pairs = [align(histories[0], component, max_age_seconds)[0] for component in histories[1:]]
    rows = []
    for index, point in enumerate(sorted(histories[0].points, key=lambda p: p.time)):
        values = [pair[index]["right"] for pair in pairs]
        total = (
            sum((Decimal(v) for v in values if v is not None), Decimal(0))
            if all(v is not None for v in values)
            else None
        )
        rows.append(
            {
                "time": point.time.isoformat(),
                "left": str(point.price),
                "right": str(total) if total is not None else None,
                "spread_pp": str((point.price - total) * 100) if total is not None else None,
            }
        )
    return rows, [
        "Synthetic spread is target YES minus summed component YES prices; it is not executable profit. All components require like-type observations within 120 seconds."
    ]
