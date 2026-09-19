from decimal import Decimal

from prediction_terminal.domain.books import BookLevel, BookSnapshot, Quote


def levels(rows: list, descending: bool = False) -> list[BookLevel]:
    merged: dict[Decimal, Decimal] = {}
    for row in rows:
        p, q = (row["price"], row["size"]) if isinstance(row, dict) else row
        p, q = Decimal(str(p)), Decimal(str(q))
        if not p.is_finite() or not q.is_finite() or not 0 <= p <= 1 or q < 0:
            raise ValueError("Invalid upstream book level")
        if q > 0:
            merged[p] = merged.get(p, Decimal(0)) + q
    return [BookLevel(price=p, quantity=q) for p, q in sorted(merged.items(), reverse=descending)]


def complement(bids: list[BookLevel]) -> list[BookLevel]:
    return sorted(
        [BookLevel(price=1 - b.price, quantity=b.quantity) for b in bids], key=lambda level: level.price
    )


def quote(book: BookSnapshot, side: str = "YES") -> Quote:
    bids, asks = (book.yes_bids, book.yes_asks) if side == "YES" else (book.no_bids, book.no_asks)
    bid, ask = (bids[0].price if bids else None), (asks[0].price if asks else None)
    return Quote(
        bid=bid,
        ask=ask,
        midpoint=(bid + ask) / 2 if bid is not None and ask is not None and bid <= ask else None,
    )
