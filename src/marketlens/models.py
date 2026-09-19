from datetime import datetime, timezone
from math import isfinite

from pydantic import BaseModel, Field


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def price(value):
    if value is None or value == "":
        return None
    try:
        number = float(value)
        return number if isfinite(number) and 0 <= number <= 1 else None
    except (ValueError, TypeError):
        return None


class Market(BaseModel):
    platform: str
    id: str
    event_id: str
    title: str
    outcome: str
    url: str
    rules: str = ""
    close_time: str | None = None
    active: bool = False
    probability: float | None = None
    probability_basis: str = "Unavailable"
    yes_ask: float | None = None
    no_ask: float | None = None
    yes_size: float | None = None
    no_size: float | None = None
    token_yes: str | None = None
    token_no: str | None = None
    series: str | None = None
    fetched_at: str = Field(default_factory=now)
    quote_time: str | None = None
    warnings: list[str] = Field(default_factory=list)


class Event(BaseModel):
    platform: str
    id: str
    title: str
    markets: list[Market] = Field(default_factory=list)
