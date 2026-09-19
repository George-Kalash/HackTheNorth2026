from dataclasses import dataclass
from decimal import ROUND_CEILING, Decimal

from prediction_terminal.domain.books import BookLevel


@dataclass(frozen=True)
class FeePolicy:
    venue: str
    market_id: str
    version: str = "unknown"
    evidence: str = ""
    known: bool = False
    mode: str = "taker"
    formula: str = "unknown"
    rate: Decimal = Decimal(0)
    effective_at: str = ""
    rounding: Decimal = Decimal(".01")

    def calculate(self, levels: list[BookLevel]) -> Decimal | None:
        if not self.known:
            return None
        if self.formula == "zero":
            return Decimal(0)
        if self.formula == "quadratic":
            # Conservative per-price-level rounding; actual per-fill rounding may differ.
            return sum(
                (
                    (self.rate * level.quantity * level.price * (1 - level.price)).quantize(
                        self.rounding, rounding=ROUND_CEILING
                    )
                    for level in levels
                ),
                Decimal(0),
            )
        if self.formula == "notional":
            return sum((self.rate * level.quantity * level.price for level in levels), Decimal(0)).quantize(
                self.rounding, rounding=ROUND_CEILING
            )
        return None
