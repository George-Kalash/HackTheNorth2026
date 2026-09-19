from decimal import Decimal
from typing import Literal
from uuid import uuid4

from pydantic import AwareDatetime, Field

from .markets import DomainModel, Price, Quantity, utcnow


class BookLevel(DomainModel):
    price: Price
    quantity: Quantity


class Quote(DomainModel):
    bid: Price | None = None
    ask: Price | None = None
    midpoint: Price | None = None


class BookSnapshot(DomainModel):
    id: str = Field(default_factory=lambda: "book_" + uuid4().hex)
    market_id: str
    yes_bids: list[BookLevel] = Field(default_factory=list)
    yes_asks: list[BookLevel] = Field(default_factory=list)
    no_bids: list[BookLevel] = Field(default_factory=list)
    no_asks: list[BookLevel] = Field(default_factory=list)
    venue_time: AwareDatetime | None = None
    received_at: AwareDatetime = Field(default_factory=utcnow)
    normalized_at: AwareDatetime = Field(default_factory=utcnow)
    sequence: int | None = None
    source_hash: str | None = None
    raw_source_ids: list[str] = Field(default_factory=list)
    mode: Literal["POLLED", "STREAMING", "UNAVAILABLE"] = "POLLED"
    flags: list[str] = Field(default_factory=list)
    tick_size: Decimal | None = None
    lot_size: Decimal | None = None
