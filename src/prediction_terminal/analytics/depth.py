from decimal import ROUND_FLOOR, Decimal

from prediction_terminal.domain.books import BookLevel


def consume(levels: list[BookLevel], quantity: Decimal, sell: bool = False):
    remaining, cost, consumed = quantity, Decimal(0), []
    for level in sorted(levels, key=lambda level: level.price, reverse=sell):
        take = min(remaining, level.quantity)
        if take > 0:
            consumed.append(BookLevel(price=level.price, quantity=take))
            cost += level.price * take
            remaining -= take
        if remaining == 0:
            break
    filled = quantity - remaining
    return filled, cost, consumed, cost / filled if filled else None


def capacity(levels: list[BookLevel]) -> Decimal:
    return sum((level.quantity for level in levels), Decimal(0))


def lot_floor(quantity: Decimal, lot: Decimal) -> Decimal:
    return (quantity / lot).to_integral_value(rounding=ROUND_FLOOR) * lot


def breakpoints(ladders: list[list[BookLevel]]) -> list[Decimal]:
    points = set()
    cap = min((capacity(level) for level in ladders), default=Decimal(0))
    for ladder in ladders:
        running = Decimal(0)
        for level in ladder:
            running += level.quantity
            if running <= cap:
                points.add(running)
    points.add(cap)
    return sorted(p for p in points if p > 0)


def common_lot(lots: list[Decimal]) -> Decimal:
    """Smallest size that is a multiple of every finite decimal lot."""
    from math import lcm

    if not lots or any(not x.is_finite() or x <= 0 for x in lots):
        raise ValueError("Lots must be finite and positive")
    places = max((-int(x.as_tuple().exponent) for x in lots), default=0)
    scale = 10**places
    return Decimal(lcm(*(int(x * scale) for x in lots))) / scale
