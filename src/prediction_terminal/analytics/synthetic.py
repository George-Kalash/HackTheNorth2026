from decimal import Decimal

from prediction_terminal.domain.markets import utcnow
from prediction_terminal.domain.opportunities import Opportunity, TradeLeg
from prediction_terminal.market_data.freshness import eligibility
from prediction_terminal.matching.synthetic import validate_replication

from .capital import roi
from .depth import breakpoints, capacity, common_lot, consume, lot_floor
from .payoffs import basket_scenarios, minimum_payout


def simulate_basket(match, markets, books, policies, request, max_age=45, max_skew=20, compute_capacity=True):
    reasons = eligibility(books, utcnow(), max_age, max_skew)
    matrix = match.replication or {}
    errors = (
        validate_replication(
            {s: p[0] for s, p in matrix.items()},
            [{s: p[i] for s, p in matrix.items()} for i in range(1, len(markets))],
        )
        if matrix
        else ["No complete replication matrix"]
    )
    reasons += errors
    approved = (
        not errors and match.review_state == "APPROVED" and match.classification == "SYNTHETIC_EQUIVALENT"
    )
    if not approved:
        reasons.append("Synthetic equivalence unapproved; losing divergence scenario included")
    if any(match.rule_hashes.get(m.id) != m.settlement.rule_hash for m in markets):
        approved = False
        reasons.append("Rule versions changed")
    if any(m.settlement.payout != 1 for m in markets):
        approved = False
        reasons.append("Non-unit contract payouts require a weighted replication model")
    if len({m.settlement.currency for m in markets}) > 1:
        if not request.currency_basis:
            approved = False
        reasons.append("Payout denominations differ; explicit currency basis risk")
    legs = []
    caps = []
    q = request.quantity
    for index, (m, b, policy) in enumerate(zip(markets, books, policies)):
        side = ("YES" if index == 0 else "NO") if request.reverse else ("NO" if index == 0 else "YES")
        asks = b.yes_asks if side == "YES" else b.no_asks
        bids = b.yes_bids if side == "YES" else b.no_bids
        filled, cost, used, vwap = consume(asks, q)
        caps.append(capacity(asks))
        fees = (
            policy.calculate(used)
            if policy.market_id == m.id and policy.venue == m.venue and policy.mode == "taker"
            else None
        )
        lot = b.lot_size or m.lot_size
        if not lot or q < lot or q % lot:
            reasons.append(f"{m.venue}: unsupported or unknown minimum lot")
        if not m.active:
            reasons.append(f"{m.venue}: inactive market")
        if filled != q:
            reasons.append(f"{m.id}: insufficient depth")
        if fees is None:
            reasons.append(f"{m.id}: unknown fee policy")
        unwind_filled, unwind, _, _ = consume(bids, filled, sell=True)
        legs.append(
            TradeLeg(
                market_id=m.id,
                venue=m.venue,
                side=side,
                quantity=q,
                filled=filled,
                consumed=used,
                cost=cost,
                vwap=vwap,
                fees=fees,
                fee_version=policy.version,
                cash_required=cost + fees if fees is not None else None,
                unwind_proceeds=unwind if unwind_filled == filled else None,
                unwind_loss_before_fees=cost - unwind if unwind_filled == filled else None,
            )
        )
    scenarios = (
        basket_scenarios(matrix, q, request.reverse)
        if matrix and all(leg.filled == q for leg in legs)
        else []
    )
    if scenarios and not approved:
        from prediction_terminal.domain.opportunities import PayoffScenario

        scenarios.append(
            PayoffScenario(
                name="Unresolved rule divergence: all legs lose",
                payouts=[Decimal(0)] * len(legs),
                total=Decimal(0),
            )
        )
    floor = minimum_payout(scenarios)
    gross = sum((leg.cost for leg in legs), Decimal(0))
    fees = (
        sum((leg.fees or Decimal(0) for leg in legs), Decimal(0))
        if all(leg.fees is not None for leg in legs)
        else request.manual_total_fees
    )
    costs = request.other_costs + request.stress_per_share * q
    net = floor - gross - fees - costs if fees is not None and scenarios else None
    result = Opportunity(
        match_id=match.id,
        direction="REVERSE BASKET" if request.reverse else "FORWARD BASKET",
        quantity=q,
        legs=legs,
        scenarios=scenarios,
        gross_outlay=gross,
        minimum_payout=floor,
        gross_floor=floor - gross,
        estimated_net_floor=net,
        roi=roi(net, gross + fees + costs if fees is not None else None),
        capacity=min(caps, default=Decimal(0)),
        verified=not reasons and net is not None,
        eligibility_reasons=reasons,
        assumptions=[
            "Scenario coverage and rule equivalence require explicit review.",
            "Basket fills are not atomic; each leg has directional exposure.",
            "Depth includes price impact; stress is separate.",
        ],
        cost_assumptions={
            "other_costs": str(request.other_costs),
            "adverse_move_per_share": str(request.stress_per_share),
            "manual_total_fees": str(request.manual_total_fees),
            "currency_basis_1_to_1": str(request.currency_basis),
        },
        book_ids=[b.id for b in books],
        book_times=[(b.venue_time or b.received_at).isoformat() for b in books],
        rule_hashes=match.rule_hashes,
    )

    if compute_capacity and result.verified:
        ladders = [(b.yes_asks if ((i == 0) == request.reverse) else b.no_asks) for i, b in enumerate(books)]
        lot = common_lot([b.lot_size or m.lot_size or Decimal(1) for m, b in zip(markets, books)])

        def profitable(q):
            if q <= 0:
                return False
            outcome = simulate_basket(
                match,
                markets,
                books,
                policies,
                request.model_copy(update={"quantity": q}),
                max_age,
                max_skew,
                False,
            )
            return (
                outcome.verified
                and outcome.estimated_net_floor is not None
                and outcome.estimated_net_floor >= request.min_edge * q
            )

        best, previous = Decimal(0), Decimal(0)
        for point in breakpoints(ladders):
            end = lot_floor(min(point, result.capacity), lot)
            if profitable(end):
                best = max(best, end)
            elif end > previous and profitable(max(lot, previous)):
                low, high = max(lot, previous), end
                while high - low > lot:
                    mid = lot_floor((low + high) / 2, lot)
                    if profitable(mid):
                        low = mid
                    else:
                        high = mid
                best = max(best, low)
            previous = end
        result.max_size_at_threshold = best
    return result
