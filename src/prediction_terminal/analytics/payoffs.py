from decimal import Decimal

from prediction_terminal.domain.opportunities import PayoffScenario


def paired_scenarios(quantity: Decimal, equivalent: bool):
    rows = [
        PayoffScenario(name="Both resolve YES", payouts=[quantity, Decimal(0)], total=quantity),
        PayoffScenario(name="Both resolve NO", payouts=[Decimal(0), quantity], total=quantity),
    ]
    if not equivalent:
        rows += [
            PayoffScenario(
                name="Rules diverge: both legs lose", payouts=[Decimal(0), Decimal(0)], total=Decimal(0)
            ),
            PayoffScenario(
                name="Rules diverge: both legs win", payouts=[quantity, quantity], total=2 * quantity
            ),
        ]
    return rows


def minimum_payout(scenarios: list[PayoffScenario]) -> Decimal:
    return min((s.total for s in scenarios), default=Decimal(0))


def basket_scenarios(replication: dict[str, list[Decimal]], quantity: Decimal, reverse: bool):
    """Matrix holds target YES then basket YES payouts. Default buys target NO + basket YES."""
    rows = []
    for state, yes_payouts in replication.items():
        values = (
            ([yes_payouts[0]] + [1 - p for p in yes_payouts[1:]])
            if reverse
            else ([1 - yes_payouts[0]] + yes_payouts[1:])
        )
        payouts = [p * quantity for p in values]
        rows.append(PayoffScenario(name=state, payouts=payouts, total=sum(payouts, Decimal(0))))
    return rows
