from decimal import Decimal

from prediction_terminal.domain.books import BookLevel


class BookBuilder:
    """Sequenced feed replay. Unsequenced updates invalidate instead of inventing ordering."""

    def __init__(self):
        self.sequence: int | None = None
        self.ready = False
        self.levels: dict[Decimal, Decimal] = {}

    def snapshot(self, levels: list[BookLevel], sequence: int | None):
        self.levels = {level.price: level.quantity for level in levels}
        self.sequence, self.ready = sequence, True

    def delta(self, price: Decimal, quantity: Decimal, sequence: int | None, absolute: bool = True) -> str:
        if sequence is None or self.sequence is None:
            self.ready = False
            return "RESNAPSHOT"
        if sequence <= self.sequence:
            return "DUPLICATE"
        if not self.ready or sequence != self.sequence + 1:
            self.ready = False
            return "GAP"
        if not absolute:
            quantity = self.levels.get(price, Decimal(0)) + quantity
        if quantity < 0:
            self.ready = False
            return "INVALID"
        if quantity == 0:
            self.levels.pop(price, None)
        else:
            self.levels[price] = quantity
        self.sequence = sequence
        return "APPLIED"

    def disconnect(self):
        self.ready = False
