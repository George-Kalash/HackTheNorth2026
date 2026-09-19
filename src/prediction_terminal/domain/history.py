from typing import Literal

from pydantic import AwareDatetime, Field

from .markets import DomainModel, Price, utcnow

PriceType = Literal["midpoint", "last_trade", "indicative", "bid", "ask"]


class PricePoint(DomainModel):
    time: AwareDatetime
    price: Price


class PriceHistory(DomainModel):
    market_id: str
    price_type: PriceType
    source: str
    points: list[PricePoint]
    interval_seconds: int
    fetched_at: AwareDatetime = Field(default_factory=utcnow)
    warnings: list[str] = Field(default_factory=list)
