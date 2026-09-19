from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from prediction_terminal.domain.books import BookSnapshot, Quote
from prediction_terminal.domain.history import PriceHistory
from prediction_terminal.domain.markets import Event, VenueMarket
from prediction_terminal.domain.matches import MatchGroup
from prediction_terminal.domain.opportunities import SimulationInputs
from prediction_terminal.domain.workspace import WorkspaceState


class DTO(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ImportRequest(DTO):
    url: str = Field(min_length=10, max_length=1000)


class SearchResponse(DTO):
    events: list[Event]
    matches: list[MatchGroup]
    errors: list[str]
    coverage: str


class SimulationRequest(SimulationInputs):
    pass


class WatchlistRequest(DTO):
    name: str = Field(min_length=1, max_length=100)
    match_ids: list[str] = Field(default_factory=list, max_length=500)


class WorkspaceRequest(DTO):
    schema_version: Literal[1] = 1
    name: str = Field(default="Research", min_length=1, max_length=100)
    state: WorkspaceState


class AlertRequest(DTO):
    name: str = Field(min_length=1, max_length=100)
    match_id: str | None = None
    min_net_floor: Decimal = Field(ge=0, allow_inf_nan=False)
    cooldown_seconds: int = Field(default=300, ge=30, le=86400)
    enabled: bool = True


class FeePolicyRequest(DTO):
    formula: Literal["zero", "quadratic", "notional"]
    rate: Decimal = Field(ge=0, le=1, allow_inf_nan=False)
    rounding: Decimal = Field(default=Decimal(".01"), gt=0, le=1, allow_inf_nan=False)
    evidence: str = Field(min_length=40, max_length=4000)
    expires_at: str


class AlignedPoint(DTO):
    time: str
    left: str
    right: str | None
    spread_pp: str | None


class ComparisonResponse(DTO):
    match: MatchGroup
    markets: list[VenueMarket]
    books: list[BookSnapshot]
    quotes: list[Quote]
    indicative_gap_pp: str | None
    histories: list[PriceHistory]
    aligned: list[AlignedPoint]
    history_warnings: list[str]
    eligibility_reasons: list[str]
    errors: list[str]
    received_at: str
    mode: str


class ScannerRowResponse(DTO):
    match: MatchGroup
    event: str
    quotes: list[Quote]
    gap_pp: str | None
    proposed_legs: list[str]
    ages: list[float]
    expiry: str | None
    fee_status: str
    verified: bool
    net_floor: str | None
    capacity: str | None
    eligibility_reasons: list[str]


class ScannerResponse(DTO):
    items: list[ScannerRowResponse]
    total: int
    limit: int
    offset: int


class SyntheticMappingRequest(DTO):
    name: str = Field(min_length=3, max_length=150)
    target_market_id: str
    basket_market_ids: list[str] = Field(min_length=2, max_length=10)
    scenario_yes_payouts: dict[str, list[Decimal]]
    coverage_evidence: str = Field(min_length=40, max_length=4000)
