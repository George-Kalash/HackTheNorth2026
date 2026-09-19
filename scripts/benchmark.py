"""Deterministic fictional workload; network/database timing intentionally excluded."""

import json
import platform
import statistics
import time
from decimal import Decimal
from pathlib import Path

from prediction_terminal.analytics.fees import FeePolicy
from prediction_terminal.analytics.opportunities import simulate
from prediction_terminal.domain.books import BookSnapshot
from prediction_terminal.domain.markets import Outcome, SettlementSpec, VenueMarket
from prediction_terminal.domain.matches import MatchGroup
from prediction_terminal.market_data.normalizer import levels


def main():
    spec = SettlementSpec(rule_text="FICTIONAL BENCHMARK", rule_hash="benchmark")
    markets = [
        VenueMarket(
            id=str(i),
            venue=v,
            external_id=str(i),
            event_id="fictional",
            title="FICTIONAL",
            outcome="YES",
            source_url="https://example.invalid",
            outcomes=[Outcome(name="YES"), Outcome(name="NO")],
            settlement=spec,
            active=True,
            lot_size=Decimal(1),
        )
        for i, v in enumerate(["kalshi", "polymarket"])
    ]
    books = [
        BookSnapshot(
            market_id=m.id,
            yes_bids=levels([[str(Decimal(".50") - Decimal(j) / 1000), "100"] for j in range(50)], True),
            no_bids=levels([[".4", "100"]]),
            yes_asks=levels([[str(Decimal(".54") + Decimal(j) / 1000), "100"] for j in range(50)]),
            no_asks=levels([[str(Decimal(".43") + Decimal(j) / 1000), "100"] for j in range(50)]),
            lot_size=Decimal(1),
        )
        for m in markets
    ]
    match = MatchGroup(
        id="fixture",
        title="FICTIONAL",
        market_ids=["0", "1"],
        classification="EXACT",
        review_state="APPROVED",
        score=1,
        reasons=[],
        differences=[],
        rule_hashes={m.id: "benchmark" for m in markets},
    )
    policies = [FeePolicy(m.venue, m.id, known=True, formula="zero", version="fictional") for m in markets]
    samples = []
    for _ in range(1000):
        start = time.perf_counter()
        simulate(match, markets, books, policies, Decimal(100), compute_capacity=False)
        samples.append((time.perf_counter() - start) * 1000)
    receipt = {
        "hardware": platform.platform() + " / " + platform.machine(),
        "python": platform.python_version(),
        "workload": "1000 fictional two-leg simulations; 50 ask levels/leg; size=100; capacity search disabled",
        "samples": len(samples),
        "p50_ms": statistics.median(samples),
        "p95_ms": sorted(samples)[949],
        "scope": "Pure local calculation only. Not calculation-to-browser latency or venue freshness.",
    }
    Path("data/benchmark.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
