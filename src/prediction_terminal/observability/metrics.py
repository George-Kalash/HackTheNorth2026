import time
from collections import Counter, deque


class Metrics:
    def __init__(self):
        self.counts: Counter[str] = Counter()
        self.latencies: deque[float] = deque(maxlen=1000)
        self.started = time.monotonic()

    def snapshot(self):
        return {
            "counts": dict(self.counts),
            "request_samples": len(self.latencies),
            "uptime_seconds": round(time.monotonic() - self.started, 1),
        }
