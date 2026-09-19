from decimal import Decimal

from prediction_terminal.analytics.opportunities import simulate
from prediction_terminal.analytics.synthetic import simulate_basket
from prediction_terminal.domain.books import BookSnapshot
from prediction_terminal.domain.matches import MatchGroup
from prediction_terminal.domain.opportunities import SimulationInputs
from prediction_terminal.market_data.normalizer import quote

from .fee_policies import policy_for


class ScannerService:
    def __init__(self, comparison, repo, settings):
        self.comparison = comparison
        self.repo = repo
        self.settings = settings

    def rows(
        self,
        limit=100,
        offset=0,
        query="",
        review_state="",
        classification="",
        max_age=45,
        quantity=Decimal(10),
        min_capacity=Decimal(0),
        min_net_edge=None,
    ):
        rows = []
        from prediction_terminal.domain.markets import utcnow

        for raw in self.repo.list("match_groups", 10000):
            match = MatchGroup.model_validate(raw)
            if review_state and match.review_state != review_state:
                continue
            if classification and match.classification != classification:
                continue
            markets = [self.comparison.market(i) for i in match.market_ids]
            if (
                query
                and query.lower() not in (match.title + " " + " ".join(m.title for m in markets)).lower()
            ):
                continue
            books = [
                BookSnapshot.model_validate(b)
                if (b := self.repo.latest_book(id))
                else BookSnapshot(market_id=id, mode="UNAVAILABLE", flags=["DISCONNECTED"])
                for id in match.market_ids
            ]
            for book in books:
                state = self.repo.get("ingestion_checkpoints", "feed_" + book.market_id)
                if state and state.get("error"):
                    book.flags = list(set(book.flags + ["DISCONNECTED"]))
            policies = [policy_for(self.repo, m) for m in markets]
            simulations = (
                [
                    simulate(
                        match,
                        markets,
                        books,
                        policies,
                        quantity,
                        reverse=reverse,
                        max_age=min(max_age, self.settings.max_age_seconds),
                        max_skew=self.settings.max_skew_seconds,
                        compute_capacity=False,
                    )
                    for reverse in [False, True]
                ]
                if len(markets) == 2
                else [
                    simulate_basket(
                        match,
                        markets,
                        books,
                        policies,
                        SimulationInputs(match_id=match.id, quantity=quantity, reverse=reverse),
                        min(max_age, self.settings.max_age_seconds),
                        self.settings.max_skew_seconds,
                        compute_capacity=False,
                    )
                    for reverse in [False, True]
                ]
            )
            best = max(
                simulations,
                key=lambda s: (
                    s.verified,
                    s.estimated_net_floor if s.estimated_net_floor is not None else Decimal("-Infinity"),
                ),
                default=None,
            )
            if min_capacity and (not best or best.capacity < min_capacity):
                continue
            if min_net_edge is not None and (
                not best
                or not best.verified
                or best.estimated_net_floor is None
                or best.estimated_net_floor < min_net_edge
            ):
                continue
            quotes = [quote(b).model_dump(mode="json") for b in books]
            gap = (
                (Decimal(quotes[0]["midpoint"]) - Decimal(quotes[1]["midpoint"])) * 100
                if len(quotes) == 2 and all(q["midpoint"] is not None for q in quotes)
                else None
            )
            rows.append(
                {
                    "match": match.model_dump(mode="json"),
                    "event": markets[0].title,
                    "quotes": quotes,
                    "gap_pp": str(gap) if gap is not None else None,
                    "proposed_legs": [f"Buy {leg.side} {leg.venue}" for leg in best.legs] if best else [],
                    "ages": [(utcnow() - (b.venue_time or b.received_at)).total_seconds() for b in books],
                    "expiry": min((m.close_time.isoformat() for m in markets if m.close_time), default=None),
                    "fee_status": "KNOWN" if all(p.known for p in policies) else "UNKNOWN",
                    "verified": best.verified if best else False,
                    "net_floor": str(best.estimated_net_floor)
                    if best and best.estimated_net_floor is not None
                    else None,
                    "capacity": str(best.capacity) if best else None,
                    "eligibility_reasons": best.eligibility_reasons
                    if best
                    else ["Synthetic mappings require explicit scenario simulation"],
                }
            )
        rows.sort(
            key=lambda r: (
                not r["verified"],
                -Decimal(r["net_floor"]) if r["net_floor"] is not None else Decimal("Infinity"),
                -r["match"]["score"],
                r["match"]["id"],
            )
        )
        return {"items": rows[offset : offset + limit], "total": len(rows), "limit": limit, "offset": offset}
