from prediction_terminal.domain.markets import VenueMarket
from prediction_terminal.domain.matches import MatchClass

REQUIRED = [
    "observation_start",
    "observation_end",
    "timezone",
    "variable",
    "baseline",
    "threshold",
    "inclusivity",
    "authority",
    "deadline",
    "payout",
    "currency",
    "cancellation",
    "void",
    "dispute",
]


def compare_rules(a: VenueMarket, b: VenueMarket) -> tuple[MatchClass, list[str]]:
    differences = []
    for key in REQUIRED:
        left, right = getattr(a.settlement, key), getattr(b.settlement, key)
        if left is None or right is None:
            differences.append(f"{key}: unresolved in one or both source specifications")
        elif left != right:
            differences.append(f"{key}: {left} ≠ {right}")
    if a.close_time != b.close_time:
        differences.append("Closing / end times differ; distinguish trading cutoff from observation time.")
    if a.settlement.rule_hash != b.settlement.rule_hash:
        differences.append(
            "Rule wording differs. Review rounding, emergency actions, cancellation and dispute treatment."
        )
    return ("RELATED" if differences else "EXACT"), differences
