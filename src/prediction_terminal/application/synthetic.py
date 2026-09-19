from decimal import Decimal

from prediction_terminal.domain.errors import TerminalError
from prediction_terminal.domain.markets import stable_id
from prediction_terminal.domain.matches import MatchGroup, MatchLeg
from prediction_terminal.matching.synthetic import validate_replication


def create_mapping(c, request):
    ids = [request.target_market_id, *request.basket_market_ids]
    if len(set(ids)) != len(ids):
        raise TerminalError("DUPLICATE_LEG", "Each basket contract must be distinct", 422)
    markets = [c.comparison.market(id) for id in ids]
    if any(m.venue == markets[0].venue for m in markets[1:]):
        raise TerminalError("VENUE_MISMATCH", "Basket legs must be on the opposite venue", 422)
    matrix = request.scenario_yes_payouts
    if any(
        len(p) != len(markets) or any(v not in {Decimal(0), Decimal(1)} for v in p) for p in matrix.values()
    ):
        raise TerminalError(
            "INVALID_MATRIX",
            "Each state needs one binary YES payout per market in target-then-basket order",
            422,
        )
    if "OTHER" not in matrix:
        raise TerminalError(
            "MISSING_OTHER_STATE", "Include an OTHER state covering undefined control/outcomes", 422
        )
    errors = validate_replication(
        {s: p[0] for s, p in matrix.items()},
        [{s: p[i] for s, p in matrix.items()} for i in range(1, len(markets))],
    )
    if errors:
        raise TerminalError("INVALID_REPLICATION", "; ".join(errors), 422)
    id = stable_id("match", *ids, str(sorted(matrix.items())))
    match = MatchGroup(
        id=id,
        title=request.name,
        market_ids=ids,
        classification="SYNTHETIC_EQUIVALENT",
        score=1,
        review_state="UNREVIEWED",
        reasons=[
            "Exact payoff replication within the supplied scenario universe; coverage and venue rules still require review."
        ],
        differences=["User-supplied exhaustive-state assertion: " + request.coverage_evidence],
        rule_hashes={m.id: m.settlement.rule_hash for m in markets},
        legs=[MatchLeg(market_id=m.id) for m in markets],
        replication=matrix,
    )
    c.repo.put("match_groups", id, match.model_dump(mode="json"))
    for i, leg in enumerate(match.legs):
        c.repo.put(
            "match_legs", id + "_" + str(i), leg.model_dump(mode="json"), match_id=id, market_id=leg.market_id
        )
    return match
