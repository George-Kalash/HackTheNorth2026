from datetime import datetime

from prediction_terminal.domain.books import BookSnapshot


def eligibility(
    books: list[BookSnapshot], now: datetime, max_age: float = 45, max_skew: float = 20
) -> list[str]:
    reasons = []
    times = []
    for book in books:
        time = book.venue_time or book.received_at
        times.append(time)
        age = (now - time).total_seconds()
        if age > max_age or age < -5:
            reasons.append(f"{book.market_id}: stale or future-dated book ({age:.1f}s)")
        if book.mode == "UNAVAILABLE" or any(
            f in book.flags for f in ["GAP", "DISCONNECTED", "CROSSED", "SCHEMA_ERROR", "TOKEN_TIME_SKEW"]
        ):
            reasons.append(f"{book.market_id}: degraded book")
    if len(times) > 1 and (max(times) - min(times)).total_seconds() > max_skew:
        reasons.append("Cross-venue quote time skew exceeds configured limit")
    return reasons
