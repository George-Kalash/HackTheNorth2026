from datetime import UTC, datetime
from decimal import Decimal
from hashlib import sha256
from typing import Annotated, Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

Price = Annotated[Decimal, Field(ge=0, le=1, allow_inf_nan=False)]
Quantity = Annotated[Decimal, Field(ge=0, allow_inf_nan=False)]
Venue = Literal["kalshi", "polymarket"]


def utcnow() -> datetime:
    return datetime.now(UTC)


def stable_id(kind: str, *parts: str) -> str:
    return kind + "_" + sha256("|".join(parts).encode()).hexdigest()[:24]


class DomainModel(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)


class SettlementSpec(DomainModel):
    observation_start: AwareDatetime | None = None
    observation_end: AwareDatetime | None = None
    timezone: str | None = None
    variable: str | None = None
    baseline: str | None = None
    threshold: str | None = None
    inclusivity: str | None = None
    authority: str | None = None
    deadline: AwareDatetime | None = None
    payout: Decimal = Decimal("1")
    currency: str = "USD"
    cancellation: str | None = None
    void: str | None = None
    dispute: str | None = None
    independent_control: str | None = None
    rule_text: str
    rule_hash: str


class Outcome(DomainModel):
    name: str
    token_id: str | None = None


class VenueMarket(DomainModel):
    id: str
    venue: Venue
    external_id: str
    event_id: str
    title: str
    outcome: str
    source_url: str
    series: str | None = None
    slug: str | None = None
    condition_id: str | None = None
    category: str = ""
    active: bool = False
    close_time: AwareDatetime | None = None
    outcomes: list[Outcome]
    settlement: SettlementSpec
    last_trade: Price | None = None
    indicative: Price | None = None
    tick_size: Decimal | None = None
    lot_size: Decimal | None = None
    raw_units: str = "dollars / contracts"
    fetched_at: AwareDatetime = Field(default_factory=utcnow)


class Event(DomainModel):
    id: str
    venue: Venue
    external_id: str
    title: str
    source_url: str
    markets: list[VenueMarket] = Field(default_factory=list)
