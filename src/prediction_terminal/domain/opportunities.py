from decimal import Decimal
from typing import Literal

from pydantic import Field

from .books import BookLevel
from .markets import DomainModel


class TradeLeg(DomainModel):
    market_id: str
    venue: str
    side: Literal["YES", "NO"]
    quantity: Decimal
    filled: Decimal
    consumed: list[BookLevel]
    cost: Decimal
    vwap: Decimal | None
    fees: Decimal | None
    fee_version: str
    cash_required: Decimal | None
    unwind_proceeds: Decimal | None = None
    unwind_loss_before_fees: Decimal | None = None


class PayoffScenario(DomainModel):
    name: str
    payouts: list[Decimal]
    total: Decimal


class Opportunity(DomainModel):
    match_id: str
    direction: str
    quantity: Decimal
    legs: list[TradeLeg]
    scenarios: list[PayoffScenario]
    gross_outlay: Decimal
    minimum_payout: Decimal
    gross_floor: Decimal
    estimated_net_floor: Decimal | None
    roi: Decimal | None
    capacity: Decimal
    max_size_at_threshold: Decimal | None = None
    verified: bool = False
    eligibility_reasons: list[str]
    assumptions: list[str]
    book_ids: list[str]
    book_times: list[str]
    rule_hashes: dict[str, str]
    model_version: str = "depth-payoff-v1"
    cost_assumptions: dict[str, str] = Field(default_factory=dict)


class SimulationInputs(DomainModel):
    budget: Decimal | None = Field(default=None, gt=0, le=1000000, allow_inf_nan=False)
    match_id: str
    quantity: Decimal = Field(default=Decimal(10), gt=0, le=1000000, allow_inf_nan=False)
    reverse: bool = False
    other_costs: Decimal = Field(default=Decimal(0), ge=0, le=100000, allow_inf_nan=False)
    stress_per_share: Decimal = Field(default=Decimal(0), ge=0, le=1, allow_inf_nan=False)
    manual_total_fees: Decimal | None = Field(default=None, ge=0, le=100000, allow_inf_nan=False)
    currency_basis: bool = False
    min_edge: Decimal = Field(default=Decimal(0), ge=0, le=1, allow_inf_nan=False)
