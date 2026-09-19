from decimal import Decimal as D

import pytest

from prediction_terminal.domain.errors import TerminalError
from prediction_terminal.domain.matches import ReviewRecord
from prediction_terminal.matching.equivalence import compare_rules
from prediction_terminal.matching.predicates import bucket
from prediction_terminal.matching.review import EVIDENCE_FIELDS, invalidate, review
from prediction_terminal.matching.synthetic import validate_replication


def test_senate_requires_dd_plus_rd():
    # First letter = House control; second = Senate. Other/undefined is explicit.
    target = {"DD": D(1), "RD": D(1), "DR": D(0), "RR": D(0), "OTHER": D(0)}
    dd = {s: D(s == "DD") for s in target}
    rd = {s: D(s == "RD") for s in target}
    assert validate_replication(target, [dd])
    assert validate_replication(target, [dd, rd]) == []
    assert validate_replication(target, [dd, dd, rd])
    assert validate_replication(target, [{"DD": D(1)}])


def test_fed_bucket_boundaries_are_not_proof(pair):
    assert bucket("Fed Cut >25bps") == "cut_large"
    assert bucket("Fed 50+ bps decrease") == "cut_large"
    a, b = pair[0]
    a.settlement.threshold = ">25"
    b.settlement = b.settlement.model_copy(update={"threshold": ">=50"})
    cls, diffs = compare_rules(a, b)
    assert cls == "RELATED"
    assert any("threshold" in d for d in diffs)


def test_rule_change_revokes(pair):
    m = invalidate(pair[2], "a", "changed")
    assert m.review_state == "REVOKED" and m.classification == "RELATED"


def test_review_requires_evidence_and_current_hashes(pair):
    match = pair[2]
    record = ReviewRecord(
        match_id=match.id,
        action="approve",
        reason="Checked all settlement terms",
        rule_hashes=match.rule_hashes,
    )
    with pytest.raises(TerminalError):
        review(match, record)
    record.evidence = {key: "Fictional evidence reference for both venues" for key in EVIDENCE_FIELDS}
    assert review(match, record).review_state == "APPROVED"
    record.rule_hashes = {"a": "old"}
    with pytest.raises(TerminalError):
        review(match, record)


def test_synthetic_senate_scenarios_are_constant():
    from prediction_terminal.analytics.payoffs import basket_scenarios

    matrix = {
        "DD": [D(1), D(1), D(0)],
        "RD": [D(1), D(0), D(1)],
        "DR": [D(0), D(0), D(0)],
        "RR": [D(0), D(0), D(0)],
        "OTHER": [D(0), D(0), D(0)],
    }
    assert {s.total for s in basket_scenarios(matrix, D(10), False)} == {D(10)}
    assert {s.total for s in basket_scenarios(matrix, D(10), True)} == {D(20)}
