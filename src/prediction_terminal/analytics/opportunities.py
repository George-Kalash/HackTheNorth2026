from decimal import Decimal

from prediction_terminal.domain.books import BookSnapshot
from prediction_terminal.domain.markets import VenueMarket, utcnow
from prediction_terminal.domain.matches import MatchGroup
from prediction_terminal.domain.opportunities import Opportunity, TradeLeg
from prediction_terminal.market_data.freshness import eligibility

from .capital import roi
from .depth import breakpoints, capacity, common_lot, consume, lot_floor
from .fees import FeePolicy
from .payoffs import minimum_payout, paired_scenarios


def simulate(
    match: MatchGroup,
    markets: list[VenueMarket],
    books: list[BookSnapshot],
    policies: list[FeePolicy],
    quantity: Decimal,
    reverse: bool = False,
    other_costs: Decimal = Decimal(0),
    stress_per_share: Decimal = Decimal(0),
    fee_override: Decimal | None = None,
    currency_basis: bool = False,
    max_age: float = 45,
    max_skew: float = 20,
    min_edge: Decimal = Decimal(0),
    compute_capacity: bool = True,
) -> Opportunity:
    indices = [1, 0] if reverse else [0, 1]
    ordered = [(markets[i], books[i], policies[i], side) for i, side in zip(indices, ["YES", "NO"])]
    reasons = eligibility(books, utcnow(), max_age, max_skew)
    approved = match.review_state == "APPROVED" and match.classification in {"EXACT", "SYNTHETIC_EQUIVALENT"}
    if not approved:
        reasons.append("Settlement mapping is not explicitly approved as equivalent")
    if any(match.rule_hashes.get(m.id) != m.settlement.rule_hash for m in markets):
        approved = False
        reasons.append("Rule version changed; approval invalid")
    if len({m.settlement.currency for m in markets}) > 1:
        reasons.append("Payout denominations differ; stablecoin/FX basis is an assumption")
        if not currency_basis:
            reasons.append("No 1:1 currency basis assumption selected")
    if any(m.settlement.payout != 1 for m in markets):
        approved = False
        reasons.append("Only $1 payout units are supported by this paired simulator")
    legs, ladders = [], []
    for m, b, policy, side in ordered:
        asks = b.yes_asks if side == "YES" else b.no_asks
        bids = b.yes_bids if side == "YES" else b.no_bids
        ladders.append(asks)
        lot = b.lot_size or m.lot_size
        if lot is None:
            reasons.append(f"{m.venue}: minimum lot size unknown")
        elif quantity < lot or quantity % lot:
            reasons.append(f"{m.venue}: size must be a multiple of minimum lot {lot}")
        if not m.active:
            reasons.append(f"{m.venue}: market is not active")
        filled, cost, used, vwap = consume(asks, quantity)
        if filled != quantity:
            reasons.append(f"{m.venue} {side}: insufficient depth ({filled}/{quantity})")
        policy_matches = policy.market_id == m.id and policy.venue == m.venue and policy.mode == "taker"
        fees = policy.calculate(used) if policy_matches else None
        if fees is None:
            reasons.append(f"{m.venue}: fee policy unknown; net economics unverified")
        unwind_filled, unwind, _, _ = consume(bids, filled, sell=True)
        legs.append(
            TradeLeg(
                market_id=m.id,
                venue=m.venue,
                side=side,
                quantity=quantity,
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
    gross = sum((leg.cost for leg in legs), Decimal(0))
    complete = all(level.filled == quantity for level in legs)
    scenarios = (
        paired_scenarios(
            quantity, approved and (currency_basis or len({m.settlement.currency for m in markets}) == 1)
        )
        if complete
        else []
    )
    floor = minimum_payout(scenarios)
    known_fees = all(level.fees is not None for level in legs)
    fees = sum((level.fees or Decimal(0) for level in legs), Decimal(0)) if known_fees else fee_override
    net = (
        floor - gross - fees - other_costs - stress_per_share * quantity
        if fees is not None and complete
        else None
    )
    if fee_override is not None and not known_fees:
        reasons.append("Manual total fee assumption is scenario-only, not a verified fee policy")
    cap = min((capacity(level) for level in ladders), default=Decimal(0))
    verified = not reasons and net is not None
    result = Opportunity(
        match_id=match.id,
        direction="REVERSE" if reverse else "FORWARD",
        quantity=quantity,
        legs=legs,
        scenarios=scenarios,
        gross_outlay=gross,
        minimum_payout=floor,
        gross_floor=floor - gross,
        estimated_net_floor=net,
        roi=roi(net, gross + fees + other_costs if fees is not None else None),
        capacity=cap,
        verified=verified,
        eligibility_reasons=list(dict.fromkeys(reasons)),
        assumptions=[
            "Buy at asks; depth already includes price impact.",
            "Positions are not atomic; a single filled leg creates directional exposure.",
            "Unwind estimate uses current bids, excludes fees and future price changes.",
            "Platform failure, settlement and payout risks remain.",
        ],
        book_ids=[b.id for b in books],
        book_times=[(b.venue_time or b.received_at).isoformat() for b in books],
        rule_hashes=match.rule_hashes,
        cost_assumptions={
            "other_costs": str(other_costs),
            "adverse_move_per_share": str(stress_per_share),
            "manual_total_fees": str(fee_override),
            "currency_basis_1_to_1": str(currency_basis),
        },
    )
    # Size search uses all cumulative depth breakpoints and lot-level bisection within each interval.
    if (
        compute_capacity
        and known_fees
        and approved
        and all((b.lot_size or m.lot_size) for m, b in zip(markets, books))
    ):
        lot = common_lot([b.lot_size or m.lot_size or Decimal(1) for m, b in zip(markets, books)])

        def profitable(q):
            if q <= 0:
                return False
            r = simulate(
                match,
                markets,
                books,
                policies,
                q,
                reverse,
                other_costs,
                stress_per_share,
                fee_override,
                currency_basis,
                max_age,
                max_skew,
                min_edge,
                False,
            )
            return r.verified and r.estimated_net_floor is not None and r.estimated_net_floor >= min_edge * q

        best = Decimal(0)
        previous = Decimal(0)
        for point in breakpoints(ladders):
            end = lot_floor(point, lot)
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
