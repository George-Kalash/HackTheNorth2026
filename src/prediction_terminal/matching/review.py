from prediction_terminal.domain.errors import TerminalError
from prediction_terminal.domain.matches import MatchGroup, ReviewRecord

EVIDENCE_FIELDS = [
    "event_identity",
    "observation_window",
    "variable_baseline",
    "threshold_inclusivity",
    "authority",
    "cancellation_void_dispute",
    "currency_payout",
]


def review(match: MatchGroup, record: ReviewRecord) -> MatchGroup:
    if record.rule_hashes != match.rule_hashes:
        raise TerminalError("RULE_VERSION_CONFLICT", "Rules changed; reload before reviewing.", 409)
    updated = match.model_copy(deep=True)
    if record.action == "approve":
        if updated.classification == "REJECTED":
            raise TerminalError("REJECTED_MAPPING", "Create a new review after correcting the mapping.", 409)
        missing = [key for key in EVIDENCE_FIELDS if len(record.evidence.get(key, "").strip()) < 10]
        if missing:
            raise TerminalError("MISSING_EVIDENCE", "Document evidence for: " + ", ".join(missing), 422)
        if len(match.market_ids) > 2:
            from .synthetic import validate_replication

            matrix = match.replication
            if not matrix or any(len(p) != len(match.market_ids) for p in matrix.values()):
                raise TerminalError("INVALID_MATRIX", "Complete synthetic payoff matrix required", 422)
            errors = validate_replication(
                {s: p[0] for s, p in matrix.items()},
                [{s: p[i] for s, p in matrix.items()} for i in range(1, len(match.market_ids))],
            )
            if errors:
                raise TerminalError("INVALID_REPLICATION", "; ".join(errors), 422)
        # Reviewer owns semantic verification; every attestation and source hash is audited.
        updated.classification = "SYNTHETIC_EQUIVALENT" if len(match.market_ids) > 2 else "EXACT"
        updated.review_state = "APPROVED"
    elif record.action == "reject":
        updated.classification, updated.review_state = "REJECTED", "REVOKED"
    else:
        updated.review_state = "REVOKED"
    updated.review_reason = record.reason
    return updated


def invalidate(match: MatchGroup, market_id: str, rule_hash: str) -> MatchGroup:
    updated = match.model_copy(deep=True)
    if updated.rule_hashes.get(market_id) != rule_hash:
        updated.rule_hashes[market_id] = rule_hash
        updated.review_state = "REVOKED"
        updated.classification = "RELATED"
        updated.review_reason = "Upstream rules changed; prior approval revoked."
    return updated
