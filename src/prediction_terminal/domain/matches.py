from decimal import Decimal
from typing import Literal

from pydantic import Field

from .markets import DomainModel, utcnow

MatchClass = Literal["EXACT", "SYNTHETIC_EQUIVALENT", "RELATED", "REJECTED"]
ReviewState = Literal["UNREVIEWED", "APPROVED", "REVOKED"]


class MatchLeg(DomainModel):
    market_id: str
    side: Literal["YES", "NO"] = "YES"
    ratio: Decimal = Decimal("1")


class MatchGroup(DomainModel):
    replication: dict[str, list[Decimal]] | None = None
    id: str
    title: str
    market_ids: list[str]
    classification: MatchClass = "RELATED"
    review_state: ReviewState = "UNREVIEWED"
    score: float = Field(ge=0, le=1)
    reasons: list[str]
    differences: list[str]
    rule_hashes: dict[str, str]
    legs: list[MatchLeg] = Field(default_factory=list)
    review_reason: str = ""
    model_version: str = "predicate-v1"


class ReviewRecord(DomainModel):
    match_id: str
    action: Literal["approve", "reject", "revoke"]
    reason: str = Field(min_length=10, max_length=4000)
    evidence: dict[str, str] = Field(default_factory=dict)
    rule_hashes: dict[str, str]
    reviewed_at: str = Field(default_factory=lambda: utcnow().isoformat())
