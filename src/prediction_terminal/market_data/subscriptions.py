from collections import Counter


class Subscriptions:
    def __init__(self):
        self.counts: Counter[str] = Counter()

    def acquire(self, topic: str):
        self.counts[topic] += 1

    def release(self, topic: str):
        self.counts[topic] -= 1
        if self.counts[topic] <= 0:
            self.counts.pop(topic, None)

    def topics(self) -> list[str]:
        return list(self.counts)
