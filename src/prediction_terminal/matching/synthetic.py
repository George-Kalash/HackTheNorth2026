from decimal import Decimal


def validate_replication(target: dict[str, Decimal], legs: list[dict[str, Decimal]]) -> list[str]:
    """States must be exhaustive by declaration; reject overlap and missing/extra states."""
    errors = []
    states = set(target)
    if not states or not legs:
        return ["Empty target or basket"]
    for leg in legs:
        if set(leg) != states:
            errors.append("Scenario coverage differs; include other/undefined states explicitly")
    if errors:
        return errors
    for state in sorted(states):
        payouts = [leg[state] for leg in legs]
        if any(p < 0 for p in payouts):
            errors.append(f"{state}: negative payout")
        if sum(payouts) != target[state]:
            errors.append(f"{state}: basket payout does not replicate target (overlap or missing coverage)")
    return errors
