from decimal import Decimal
from uuid import uuid4

from prediction_terminal.analytics.depth import capacity, common_lot, consume, lot_floor
from prediction_terminal.analytics.opportunities import simulate
from prediction_terminal.application.fee_policies import policy_for
from prediction_terminal.domain.books import BookSnapshot
from prediction_terminal.domain.errors import TerminalError


class SimulationService:
    def __init__(self, comparison, repo, settings):
        self.comparison = comparison
        self.repo = repo
        self.settings = settings

    async def run(self, request):
        match = self.comparison.match(request.match_id)
        markets = [self.comparison.market(i) for i in match.market_ids]
        data = await self.comparison.get(match.id, with_history=False)
        books = [BookSnapshot.model_validate(b) for b in data["books"]]
        policies = [policy_for(self.repo, m) for m in markets]
        quantity = request.quantity
        if request.budget is not None:
            if len(markets) > 2:
                indices = list(range(len(markets)))
                ladders = [
                    (b.yes_asks if ((i == 0) == request.reverse) else b.no_asks) for i, b in enumerate(books)
                ]
            else:
                indices = [1, 0] if request.reverse else [0, 1]
                ladders = [books[indices[0]].yes_asks, books[indices[1]].no_asks]
            lot = common_lot([books[i].lot_size or markets[i].lot_size or Decimal(".01") for i in indices])
            cap = min(capacity(ladder) for ladder in ladders)
            low, high = Decimal(0), lot_floor(cap, lot)

            def outlay(q):
                fills = [consume(ladder, q) for ladder in ladders]
                fees = [policies[i].calculate(fill[2]) for i, fill in zip(indices, fills)]
                total_fees = (
                    sum((f or Decimal(0) for f in fees), Decimal(0))
                    if all(f is not None for f in fees)
                    else request.manual_total_fees
                )
                if total_fees is None:
                    raise TerminalError(
                        "UNKNOWN_BUDGET_FEES",
                        "Budget sizing requires known fees or an explicit manual total fee assumption.",
                        422,
                    )
                return (
                    sum((f[1] for f in fills), Decimal(0))
                    + total_fees
                    + request.other_costs
                    + request.stress_per_share * q
                )

            while high - low >= lot:
                mid = lot_floor((low + high + lot) / 2, lot)
                if outlay(mid) <= request.budget:
                    low = mid
                else:
                    high = mid - lot
            quantity = low
            if quantity <= 0:
                raise TerminalError(
                    "INSUFFICIENT_BUDGET", "Budget cannot fund one modeled lot at available depth.", 422
                )
        if len(markets) > 2:
            from prediction_terminal.analytics.synthetic import simulate_basket

            result = simulate_basket(
                match,
                markets,
                books,
                policies,
                request.model_copy(update={"quantity": quantity}),
                self.settings.max_age_seconds,
                self.settings.max_skew_seconds,
            )
        else:
            result = simulate(
                match,
                markets,
                books,
                policies,
                quantity,
                request.reverse,
                request.other_costs,
                request.stress_per_share,
                request.manual_total_fees,
                request.currency_basis,
                self.settings.max_age_seconds,
                self.settings.max_skew_seconds,
                request.min_edge,
            )
        payload = result.model_dump(mode="json")
        # Embedded complete normalized inputs survive rolling book retention.
        snapshot_id = "op_" + uuid4().hex
        self.repo.put(
            "opportunity_snapshots",
            snapshot_id,
            {
                "id": snapshot_id,
                "result": payload,
                "inputs": {
                    "books": data["books"],
                    "markets": [m.model_dump(mode="json") for m in markets],
                    "match": match.model_dump(mode="json"),
                },
            },
            match_id=match.id,
        )
        return result
