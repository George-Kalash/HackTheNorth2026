from decimal import Decimal

from prediction_terminal.analytics.opportunities import simulate
from prediction_terminal.application.alerts import evaluate


class Memory:
    def __init__(self):
        self.data = {
            "alert_rules": [
                {"id": "r", "enabled": True, "match_id": None, "min_net_floor": "0", "cooldown_seconds": 300}
            ],
            "alert_events": [],
        }

    def list(self, table, limit):
        return self.data[table]

    def put(self, table, id, payload, **keys):
        self.data[table].insert(0, payload)


def test_dedup_and_unverified_suppression(pair):
    markets, books, match, fees = pair
    r = simulate(match, markets, books, fees, Decimal(1))
    repo = Memory()
    assert len(evaluate(repo, r)) == 1
    assert evaluate(repo, r) == []
    r.verified = False
    repo.data["alert_events"] = []
    assert evaluate(repo, r) == []
